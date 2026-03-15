import os
import sys
from typing import Any, Callable

from absl import flags
from flask import Flask

from mesop.runtime import enable_debug_mode
from mesop.server.constants import EDITOR_PACKAGE_PATH, PROD_PACKAGE_PATH
from mesop.server.hot_reload import start_file_watcher
from mesop.server.flags import port
from mesop.server.logging import log_startup
from mesop.server.server import configure_flask_app
from mesop.server.static_file_serving import configure_static_file_serving
from mesop.utils.host_util import get_local_host


class App:
  _flask_app: Flask

  def __init__(self, flask_app: Flask):
    self._flask_app = flask_app

  def run(self):
    log_startup(port=port())

    self._flask_app.run(host=get_local_host(), port=port(), use_reloader=False)


def create_app(
  prod_mode: bool,
  run_block: Callable[..., None] | None = None,
) -> App:
  flask_app = configure_flask_app(prod_mode=prod_mode)

  if not prod_mode:
    enable_debug_mode()

  if run_block is not None:
    run_block()

  configure_static_file_serving(
    flask_app,
    static_file_runfiles_base=PROD_PACKAGE_PATH
    if prod_mode
    else EDITOR_PACKAGE_PATH,
    disable_gzip_cache=not prod_mode,
  )

  return App(flask_app=flask_app)


def create_wsgi_app(
  *, debug_mode: bool = False, watch_path: str | None = None
):
  """
  Creates a WSGI app that can be used to run Mesop in a WSGI server like gunicorn.

  Args:
    debug_mode: If True, enables debug mode and hot reloading for the Mesop app.
    watch_path: Path to the main Python file to watch for changes. When provided
      alongside ``debug_mode=True``, a background file-watcher thread is started
      so that hot reloading works even when Mesop is mounted inside another web
      server (e.g. FastAPI). Typically set to ``__file__`` of your entry-point
      module.

      Example::

        import mesop as me
        from mesop.server.wsgi_app import create_wsgi_app

        @me.page()
        def home():
            me.text("Hello")

        mesop_app = create_wsgi_app(debug_mode=True, watch_path=__file__)
  """
  _app = None

  # Start the file watcher immediately so that changes made before the first
  # request are still detected. The watcher runs in a daemon thread and does
  # not depend on the Flask app being initialised yet.
  if debug_mode and watch_path:
    absolute_path = (
      watch_path if os.path.isabs(watch_path) else os.path.abspath(watch_path)
    )
    start_file_watcher(absolute_path, prod_mode=False)

  def wsgi_app(environ: dict[Any, Any], start_response: Callable[..., Any]):
    # Lazily create and reuse a flask app instance to avoid
    # the overhead for each WSGI request.
    nonlocal _app
    if not _app:
      # Parse the flags before creating the app otherwise you will
      # get UnparsedFlagAccessError.
      #
      # This currently parses a list without any flags because typically Mesop
      # will be run with gunicorn as a WSGI app and there may be unexpected
      # flags such as "--bind".
      #
      # Example:
      # $ gunicorn --bind :8080 main:me
      #
      # We will ignore all CLI flags, but we could provide a way to override
      # Mesop defined flags in the future if necessary.
      #
      # Note: absl-py requires the first arg (program name), and will raise an error
      # if we pass an empty list.
      flags.FLAGS(sys.argv[:1])
      _app = create_app(prod_mode=not debug_mode)

    return _app._flask_app.wsgi_app(environ, start_response)  # type: ignore

  return wsgi_app
