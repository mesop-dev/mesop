import base64
import dataclasses
import logging
import os
import secrets
import threading
import time
import types
from collections.abc import Generator, Sequence
from concurrent.futures import ThreadPoolExecutor

from flask import (
  Flask,
  Response,
  abort,
  copy_current_request_context,
  make_response,
  request,
  stream_with_context,
)
from werkzeug.middleware.proxy_fix import ProxyFix

import mesop.protos.ui_pb2 as pb
from mesop.component_helpers import diff_component
from mesop.env.env import (
  MESOP_APP_BASE_PATH,
  MESOP_BASE_URL_PATH,
  MESOP_PROD_UNREDACTED_ERRORS,
  MESOP_TRUST_PROXY_HEADERS,
  MESOP_WEBSOCKETS_ENABLED,
)
from mesop.events import LoadEvent
from mesop.exceptions import MesopDeveloperException, format_traceback
from mesop.runtime import runtime
from mesop.runtime.context import PendingCookie
from mesop.server.constants import WEB_COMPONENTS_PATH_SEGMENT
from mesop.server.server_debug_routes import configure_debug_routes
from mesop.server.server_utils import (
  STREAM_END,
  create_update_state_event,
  get_static_folder,
  get_static_url_path,
  is_same_site,
  make_sse_response,
  prefix_base_url,
  serialize,
)
from mesop.utils.async_utils import run_async_generator, run_coroutine
from mesop.utils.url_utils import remove_url_query_param
from mesop.warn import warn

UI_PATH = prefix_base_url("/__ui__")
APPLY_COOKIES_PATH = prefix_base_url("/__apply-cookies")

logger = logging.getLogger(__name__)

_COOKIE_TOKEN_TTL_SECONDS = 60


def _get_cookie_secret_key() -> str:
  """Return MESOP_COOKIE_SECRET_KEY, raising MesopDeveloperException if unset."""
  key = os.environ.get("MESOP_COOKIE_SECRET_KEY", "")
  if not key:
    raise MesopDeveloperException(
      "MESOP_COOKIE_SECRET_KEY must be set to use Mesop cookies.\n"
      "Set it as an environment variable before starting Mesop:\n"
      "  MESOP_COOKIE_SECRET_KEY=<your-secret> mesop main.py\n"
      "Generate a strong key with:\n"
      '  python -c "import secrets; print(secrets.token_hex(32))"'
    )
  return key


class _CookieTokenCache:
  """Self-contained itsdangerous-signed cookie token store.

  Each token is an itsdangerous-signed blob containing the pending cookies
  plus a one-time nonce.  Because the token carries all the data, any
  server replica that holds the same MESOP_COOKIE_SECRET_KEY can verify
  and redeem it — multi-worker deployments work without sticky sessions
  (unlike the previous ``MESOP_STATE_SESSION_BACKEND=none`` limitation,
  which required sticky sessions for state; here no sticky sessions are
  needed at all).

  **Single-use enforcement:** consumed nonces are tracked per-process in a
  small in-memory set bounded by the TTL window.  Within a single process
  replays are rejected strictly.  Across multiple workers, a token *could*
  theoretically be replayed to a different worker that has not yet seen the
  nonce, but the CSRF Origin check on ``/__apply-cookies`` and HTTPS in
  production make this impractical.

  **Note on value visibility:** the payload is signed, not encrypted, so
  cookie values are Base64-visible in the token as it passes through browser
  JavaScript.  For complete value privacy use ``@me.cookieclass(encrypted=True)``
  which Fernet-encrypts the value before it ever leaves the server.
  """

  def __init__(self) -> None:
    self._lock = threading.Lock()
    self._used_nonces: dict[str, float] = {}  # nonce -> expiry (monotonic)

  def put(self, cookies: list[PendingCookie]) -> str:
    """Sign and return a self-contained token encoding *cookies*."""
    from itsdangerous import URLSafeTimedSerializer

    payload = {
      "n": secrets.token_urlsafe(16),
      "c": [dataclasses.asdict(c) for c in cookies],
    }
    return URLSafeTimedSerializer(
      _get_cookie_secret_key(), salt="mesop-apply-cookies"
    ).dumps(payload)

  def pop(self, token: str) -> list[PendingCookie] | None:
    """Verify *token*, mark its nonce used, and return the cookie list.

    Returns ``None`` if the token is invalid, expired, or already consumed.
    """
    from itsdangerous import (
      BadSignature,
      SignatureExpired,
      URLSafeTimedSerializer,
    )

    try:
      payload = URLSafeTimedSerializer(
        _get_cookie_secret_key(), salt="mesop-apply-cookies"
      ).loads(token, max_age=_COOKIE_TOKEN_TTL_SECONDS)
    except (BadSignature, SignatureExpired):
      return None

    nonce = payload.get("n", "")
    with self._lock:
      if nonce in self._used_nonces:
        return None
      self._used_nonces[nonce] = time.monotonic() + _COOKIE_TOKEN_TTL_SECONDS
      self._evict_used_locked()

    try:
      return [PendingCookie(**c) for c in payload["c"]]
    except (TypeError, KeyError):
      return None

  def _evict_used_locked(self) -> None:
    """Discard expired nonce entries. Must be called with self._lock held."""
    now = time.monotonic()
    expired = [k for k, exp in self._used_nonces.items() if now > exp]
    for k in expired:
      del self._used_nonces[k]


_cookie_token_cache = _CookieTokenCache()


def _process_on_load_result(result) -> Generator[None, None, None]:
  """Process on_load result, handling sync generators, async generators, and coroutines."""
  if result is not None:
    if isinstance(result, types.AsyncGeneratorType):
      yield from run_async_generator(result)
    elif isinstance(result, types.CoroutineType):
      yield run_coroutine(result)
    else:
      # Regular generator
      yield from result


def configure_flask_app(
  *, prod_mode: bool = True, exceptions_to_propagate: Sequence[type] = ()
) -> Flask:
  if MESOP_WEBSOCKETS_ENABLED:
    logger.info("Experiment enabled: MESOP_WEBSOCKETS_ENABLED")

  if MESOP_APP_BASE_PATH:
    logger.info(f"MESOP_APP_BASE_PATH set to {MESOP_APP_BASE_PATH}")
  if MESOP_BASE_URL_PATH:
    logger.info(f"MESOP_BASE_URL_PATH set to {MESOP_BASE_URL_PATH}")

  if MESOP_PROD_UNREDACTED_ERRORS and prod_mode:
    logger.info(
      "MESOP_PROD_UNREDACTED_ERRORS is enabled. Showing full error details (including in prod mode)."
    )

  static_folder = get_static_folder()
  static_url_path = get_static_url_path()
  if static_folder and static_url_path:
    logger.info(f"Static folder enabled: {static_folder}")
  flask_app = Flask(
    __name__,
    static_folder=static_folder,
    static_url_path=static_url_path,
  )

  if MESOP_TRUST_PROXY_HEADERS:
    # Apply ProxyFix so that request.url_root and request.scheme reflect the
    # external-facing URL reported by the reverse proxy (X-Forwarded-Proto,
    # X-Forwarded-Host, etc.). This is required for the CSWSH/CSRF origin checks
    # to work correctly when Mesop runs behind a load balancer or cloud proxy.
    #
    # Only enabled when MESOP_TRUST_PROXY_HEADERS is set (either explicitly or
    # via auto-detection of known cloud platforms). Do NOT enable this in
    # deployments that are not behind a trusted reverse proxy, as it would allow
    # callers to spoof X-Forwarded-* headers and bypass origin checks.
    flask_app.wsgi_app = ProxyFix(  # type: ignore[method-assign]
      flask_app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1
    )

  def maybe_append_apply_cookies_command() -> None:
    """If the context has pending cookies, cache them and append an ApplyCookiesCommand."""
    pending = runtime().context().pending_cookies()
    if not pending:
      return
    token = _cookie_token_cache.put(list(pending))
    runtime().context().clear_pending_cookies()
    runtime().context().commands().append(
      pb.Command(apply_cookies=pb.ApplyCookiesCommand(token=token))
    )

  def render_loop(
    path: str,
    trace_mode: bool = False,
    init_request: bool = False,
  ) -> Generator[str, None, None]:
    try:
      runtime().context().acquire_lock()
      runtime().run_path(path=path)
      page_config = runtime().get_page_config(path=path)
      title = page_config.title if page_config else "Unknown path"

      root_component = runtime().context().current_node()
      previous_root_component = runtime().context().previous_node()
      component_diff = None
      if (
        # Disable component diffing with MESOP_WEBSOCKETS_ENABLED
        # to avoid a race condition where the previous component tree may
        # have been constructed by a concurrent event.
        not MESOP_WEBSOCKETS_ENABLED
        and not trace_mode
        and previous_root_component
      ):
        component_diff = diff_component(previous_root_component, root_component)
        root_component = None
      commands = runtime().context().commands()
      # Need to clear commands so that we don't keep on re-sending commands
      # (e.g. scroll into view) for the same context (e.g. multiple render loops
      # when processing a generator handler function)
      runtime().context().clear_commands()
      js_modules = runtime().context().js_modules()
      # Similar to above, clear JS modules after sending it once to minimize payload.
      # Although it shouldn't cause any issue because client-side, each js module
      # should only be imported once.
      runtime().context().clear_js_modules()
      data = pb.UiResponse(
        render=pb.RenderEvent(
          root_component=root_component,
          component_diff=component_diff,
          commands=commands,
          title=title,
          js_modules=[
            f"/{WEB_COMPONENTS_PATH_SEGMENT}{js_module}"
            for js_module in js_modules
          ],
        )
      )
      runtime().context().set_has_rendered(True)
      yield serialize(data)
    except Exception as e:
      logging.error(e)
      if e in exceptions_to_propagate:
        raise e
      yield from yield_errors(
        error=pb.ServerError(exception=str(e), traceback=format_traceback())
      )
    finally:
      runtime().context().release_lock()

  def yield_errors(error: pb.ServerError) -> Generator[str, None, None]:
    should_redact_errors = (
      not runtime().debug_mode and not MESOP_PROD_UNREDACTED_ERRORS
    )
    if should_redact_errors:
      error.ClearField("traceback")
      # Redact developer errors
      if "Mesop Internal Error:" in error.exception:
        error.exception = "Sorry, there was an internal error with Mesop."
      if "Mesop Developer Error:" in error.exception:
        error.exception = (
          "Sorry, there was an error. Please contact the developer."
        )

    ui_response = pb.UiResponse(error=error)

    yield serialize(ui_response)
    yield STREAM_END

  def generate_data(ui_request: pb.UiRequest) -> Generator[str, None, None]:
    try:
      # Wait for hot reload to complete on the server-side before processing the
      # request. This avoids a race condition where the client-side reloads before
      # the server has reloaded.
      runtime().wait_for_hot_reload()
      if runtime().has_loading_errors():
        # Only showing the first error since our error UI only
        # shows one error at a time, and in practice there's usually
        # one error.
        yield from yield_errors(runtime().get_loading_errors()[0])

      if ui_request.HasField("init"):
        runtime().context().set_theme_settings(ui_request.init.theme_settings)
        runtime().context().set_viewport_size(ui_request.init.viewport_size)
        runtime().context().initialize_query_params(
          ui_request.init.query_params
        )
        page_config = runtime().get_page_config(path=ui_request.path)
        if page_config and page_config.on_load:
          result = page_config.on_load(
            LoadEvent(
              path=ui_request.path,
            )
          )
          # on_load is a generator function then we need to iterate through
          # the generator object. This also handles async generators and coroutines.
          if result:
            for _ in _process_on_load_result(result):
              maybe_append_apply_cookies_command()
              yield from render_loop(path=ui_request.path, init_request=True)
              runtime().context().set_previous_node_from_current_node()
              runtime().context().reset_current_node()
          else:
            maybe_append_apply_cookies_command()
            yield from render_loop(path=ui_request.path, init_request=True)
        else:
          yield from render_loop(path=ui_request.path, init_request=True)
        if not MESOP_WEBSOCKETS_ENABLED:
          yield create_update_state_event()
        yield STREAM_END
      elif ui_request.HasField("user_event"):
        event = ui_request.user_event
        runtime().context().set_theme_settings(event.theme_settings)
        runtime().context().set_viewport_size(event.viewport_size)
        runtime().context().initialize_query_params(event.query_params)

        if not MESOP_WEBSOCKETS_ENABLED:
          if event.states.states:
            runtime().context().update_state(event.states)
          else:
            runtime().context().restore_state_from_session(event.state_token)

        # In websockets mode, since the context instance is long-lived, we only
        # need to do a trace render loop if the context has not completed at least
        # one render loop.
        if (
          not MESOP_WEBSOCKETS_ENABLED or not runtime().context().has_rendered()
        ):
          for _ in render_loop(path=ui_request.path, trace_mode=True):
            pass
        if ui_request.user_event.handler_id:
          runtime().context().set_previous_node_from_current_node()
        else:
          # Set previous node to None to skip component diffs on hot reload. This is
          # because we lose the previous state before hot reloading, which results in
          # no diff.
          #
          # This will also skip component diffs for back button events on the browser
          # since no event handler ID is provided in that case.
          runtime().context().reset_previous_node()
        runtime().context().reset_current_node()

        path = ui_request.path
        has_run_navigate_on_load = False

        if ui_request.user_event.HasField("navigation"):
          page_config = runtime().get_page_config(path=path)
          if (
            page_config and page_config.on_load and not has_run_navigate_on_load
          ):
            has_run_navigate_on_load = True
            yield from run_page_load(path=path)

        result = runtime().context().run_event_handler(ui_request.user_event)
        for _ in result:
          maybe_append_apply_cookies_command()
          navigate_commands = [
            command
            for command in runtime().context().commands()
            if command.HasField("navigate")
          ]
          if len(navigate_commands) > 1:
            warn(
              "Dedicated multiple navigate commands! Only the first one will be used."
            )
          for command in runtime().context().commands():
            if command.HasField("navigate"):
              # If opening in a new tab, don't navigate the current page
              # Just render the current page and let the frontend handle opening the new tab
              if command.navigate.open_in_new_tab:
                break
              runtime().context().initialize_query_params(
                command.navigate.query_params
              )
              if command.navigate.url.startswith(("http://", "https://")):
                yield from render_loop(path=path)
                yield STREAM_END
                return
              path = remove_url_query_param(command.navigate.url)
              page_config = runtime().get_page_config(path=path)
              if (
                page_config
                and page_config.on_load
                and not has_run_navigate_on_load
              ):
                has_run_navigate_on_load = True
                yield from run_page_load(path=path)

          yield from render_loop(path=path)
          runtime().context().set_previous_node_from_current_node()
          runtime().context().reset_current_node()
        # Flush any cookies queued by a generator handler that yielded 0 times.
        maybe_append_apply_cookies_command()
        if not MESOP_WEBSOCKETS_ENABLED:
          yield create_update_state_event(diff=True)
        yield STREAM_END
      else:
        raise Exception(f"Unknown request type: {ui_request}")

    except Exception as e:
      if e in exceptions_to_propagate:
        raise e
      # Clear any pending cookies queued by the failing handler so they do
      # not leak into the next event cycle.  This matters most in WebSockets
      # mode where the Context is long-lived across multiple requests.
      runtime().context().clear_pending_cookies()
      yield from yield_errors(
        error=pb.ServerError(exception=str(e), traceback=format_traceback())
      )

  def run_page_load(*, path: str):
    page_config = runtime().get_page_config(path=path)
    assert page_config and page_config.on_load
    result = page_config.on_load(LoadEvent(path=path))
    # on_load is a generator function then we need to iterate through
    # the generator object. This also handles async generators and coroutines.
    if result:
      for _ in _process_on_load_result(result):
        maybe_append_apply_cookies_command()
        yield from render_loop(path=path, init_request=True)
        runtime().context().set_previous_node_from_current_node()
        runtime().context().reset_current_node()

  @flask_app.route(UI_PATH, methods=["POST"])
  def ui_stream() -> Response:
    # Prevent CSRF by checking the request site matches the site
    # of the URL root (where the Flask app is being served from)
    #
    # Skip the check if it's running in debug mode because when
    # running in Colab, the UI and HTTP requests are on different sites.
    if not runtime().debug_mode and not is_same_site(
      request.headers.get("Origin"), request.url_root
    ):
      abort(403, "Rejecting cross-site POST request to " + UI_PATH)
    data = request.data
    if not data:
      raise Exception("Missing request payload")
    ui_request = pb.UiRequest()
    ui_request.ParseFromString(base64.urlsafe_b64decode(data))

    response = make_sse_response(stream_with_context(generate_data(ui_request)))
    return response

  @flask_app.route(APPLY_COOKIES_PATH, methods=["POST"])
  def apply_cookies() -> Response:
    """Endpoint that sets cookies previously queued by me.set_cookie().

    The Mesop client POSTs the token in the request body (not the URL) to keep
    it out of server access logs and browser history.  The token expires after
    _COOKIE_TOKEN_TTL_SECONDS seconds and is enforced as single-use within a
    given server process (used nonces are tracked in memory).  In multi-worker
    deployments, a replay routed to a different worker may still succeed;
    the CSRF Origin check and short TTL reduce that risk in practice.

    Same-site origin validation (matching ui_stream) prevents a cross-site
    attacker from replaying a valid token against a victim's browser.
    """
    if not runtime().debug_mode and not is_same_site(
      request.headers.get("Origin"), request.url_root
    ):
      abort(403, "Rejecting cross-site POST request to " + APPLY_COOKIES_PATH)
    token = request.form.get("t", "")
    if not token:
      abort(400, "Missing token")
    pending: list[PendingCookie] | None = _cookie_token_cache.pop(token)
    if pending is None:
      abort(400, "Invalid or expired token")

    resp = make_response("", 204)
    # Prevent intermediary caching of this tokenised response.
    resp.headers["Cache-Control"] = "no-store"
    for cookie in pending:
      resp.set_cookie(
        cookie.name,
        cookie.value,
        max_age=cookie.max_age,
        path=cookie.path,
        domain=cookie.domain,
        secure=cookie.secure,
        httponly=cookie.httponly,
        samesite=cookie.samesite,
      )
    return resp

  @flask_app.teardown_request
  def teardown_clear_stale_state_sessions(error=None):
    runtime().context().clear_stale_state_sessions()

  if not prod_mode:
    configure_debug_routes(flask_app)

  if MESOP_WEBSOCKETS_ENABLED:
    from flask_sock import Sock
    from simple_websocket import Server

    sock = Sock(flask_app)

    # Global thread pool and admission semaphore, scoped to this Flask app instance
    # so they are only created when WebSockets are actually enabled.
    #
    # _ws_executor caps the total number of OS threads processing WebSocket requests
    # across ALL connections, preventing thread exhaustion from either a single
    # flooded connection or many concurrent connections (CWE-400).
    #
    # _ws_semaphore enforces a hard limit on the total number of tasks that may be
    # in-flight at once (running + queued in the executor). Without this, a flood of
    # connections could fill the executor's unbounded internal queue, exhausting RAM.
    # acquire() is non-blocking: excess messages are dropped rather than queued.
    _WS_MAX_WORKERS = 100
    _WS_MAX_IN_FLIGHT = 500
    _ws_executor = ThreadPoolExecutor(max_workers=_WS_MAX_WORKERS)
    _ws_semaphore = threading.BoundedSemaphore(_WS_MAX_IN_FLIGHT)

    @sock.route(UI_PATH)
    def handle_websocket(ws: Server):
      # Prevent cross-site WebSocket hijacking (CSWSH). Browsers don't enforce
      # same-origin policy for WebSocket upgrades, so we validate the Origin header
      # ourselves — matching the same logic used for the SSE endpoint above.
      if not runtime().debug_mode and not is_same_site(
        request.headers.get("Origin"), request.url_root
      ):
        ws.close(message="Rejecting cross-site WebSocket request to " + UI_PATH)
        return

      def ws_generate_data(ws, ui_request):
        # Semaphore is always released here, whether generate_data succeeds or raises,
        # so the in-flight count stays accurate and slots are never leaked.
        try:
          for data_chunk in generate_data(ui_request):
            if not ws.connected:
              break
            ws.send(data_chunk)
        finally:
          _ws_semaphore.release()

      # Generate a unique session ID for the WebSocket connection
      session_id = secrets.token_urlsafe(32)
      request.websocket_session_id = session_id  # type: ignore

      try:
        while True:
          message = ws.receive()
          if not message:
            continue  # Ignore empty messages

          ui_request = pb.UiRequest()
          try:
            decoded_message = base64.urlsafe_b64decode(message)
            ui_request.ParseFromString(decoded_message)
          except Exception as parse_error:
            logging.error("Failed to parse message: %s", parse_error)
            continue  # Skip processing this message

          # Reject the message immediately if the server is already at capacity.
          # This keeps memory bounded regardless of how many connections are open.
          if not _ws_semaphore.acquire(blocking=False):
            logging.warning(
              "WebSocket server at capacity (%d in-flight tasks), dropping message.",
              _WS_MAX_IN_FLIGHT,
            )
            continue

          # Submit to the bounded thread pool rather than spawning a raw OS thread.
          # copy_current_request_context snapshots the Flask request context here
          # (in the WebSocket handler thread) so each pool task runs with the
          # correct context, even though pool threads are reused across requests.
          _ws_executor.submit(
            copy_current_request_context(ws_generate_data), ws, ui_request
          )

      except Exception as e:
        logging.error("WebSocket error: %s", e)
      finally:
        # Clean up context when connection closes
        if hasattr(request, "websocket_session_id"):
          websocket_session_id = request.websocket_session_id  # type: ignore
          runtime().delete_context(websocket_session_id)

  return flask_app
