import base64
import logging
import secrets
import threading
import types
from typing import Generator, Sequence

from flask import (
  Flask,
  Response,
  abort,
  copy_current_request_context,
  request,
  stream_with_context,
)

import mesop.protos.ui_pb2 as pb
from mesop.component_helpers import diff_component
from mesop.env.env import (
  MESOP_APP_BASE_PATH,
  MESOP_BASE_URL_PATH,
  MESOP_PROD_UNREDACTED_ERRORS,
  MESOP_WEBSOCKETS_ENABLED,
)
from mesop.events import LoadEvent
from mesop.exceptions import format_traceback
from mesop.runtime import runtime
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

logger = logging.getLogger(__name__)


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
              yield from render_loop(path=ui_request.path, init_request=True)
              runtime().context().set_previous_node_from_current_node()
              runtime().context().reset_current_node()
          else:
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
        if not MESOP_WEBSOCKETS_ENABLED:
          yield create_update_state_event(diff=True)
        yield STREAM_END
      else:
        raise Exception(f"Unknown request type: {ui_request}")

    except Exception as e:
      if e in exceptions_to_propagate:
        raise e
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

  @flask_app.teardown_request
  def teardown_clear_stale_state_sessions(error=None):
    runtime().context().clear_stale_state_sessions()

  if not prod_mode:
    configure_debug_routes(flask_app)

  if MESOP_WEBSOCKETS_ENABLED:
    from flask_sock import Sock
    from simple_websocket import Server

    sock = Sock(flask_app)

    @sock.route(UI_PATH)
    def handle_websocket(ws: Server):
      def ws_generate_data(ws, ui_request):
        for data_chunk in generate_data(ui_request):
          if not ws.connected:
            break
          ws.send(data_chunk)

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

          # Start a new thread so we can handle multiple
          # concurrent updates for the same websocket connection.
          #
          # Note: we do copy_current_request_context at the callsite
          # to ensure that the request context is copied over for each new thread.
          thread = threading.Thread(
            target=copy_current_request_context(ws_generate_data),
            args=(ws, ui_request),
            daemon=True,
          )
          thread.start()

      except Exception as e:
        logging.error("WebSocket error: %s", e)
      finally:
        # Clean up context when connection closes
        if hasattr(request, "websocket_session_id"):
          websocket_session_id = request.websocket_session_id  # type: ignore
          runtime().delete_context(websocket_session_id)

  return flask_app
