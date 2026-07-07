import logging
import sys
import threading
from typing import Sequence

from absl import app, flags

import mesop.protos.ui_pb2 as pb
from mesop.cli.execute_module import (
  clear_app_modules,
  execute_module,
  get_module_name_from_runfile_path,
)
from mesop.exceptions import format_traceback
from mesop.runtime import (
  enable_debug_mode,
  hot_reload_finished,
  reset_runtime,
  runtime,
)
from mesop.server.constants import EDITOR_PACKAGE_PATH, PROD_PACKAGE_PATH
from mesop.server.flags import port
from mesop.server.logging import log_startup
from mesop.server.server import configure_flask_app
from mesop.server.static_file_serving import configure_static_file_serving
from mesop.utils.host_util import get_public_host
from mesop.utils.runfiles import get_runfile_location

FLAGS = flags.FLAGS

flags.DEFINE_string("path", "", "path to main python module of Mesop app.")
flags.DEFINE_string(
  "static_file_runfiles_base",
  "",
  "path to dir with the static files (within runfiles).",
)
flags.DEFINE_bool(
  "prod", False, "set to true for prod mode; otherwise editor mode."
)
flags.DEFINE_bool("verbose", False, "set to true for verbose logging.")
flags.DEFINE_bool(
  "reload_demo_modules", False, "set to true to reload demo modules."
)


def execute_main_module():
  module_name = get_module_name_from_runfile_path(FLAGS.path)
  clear_app_modules(module_name=module_name)
  if FLAGS.reload_demo_modules:
    clear_demo_modules()
  execute_module(
    module_path=get_runfile_location(FLAGS.path),
    module_name=module_name,
  )


def clear_demo_modules():
  for module in demo_modules:
    if module in sys.modules:
      del sys.modules[module]


def monitor_stdin():
  while True:
    line = sys.stdin.readline().strip()
    if line == "IBAZEL_BUILD_COMPLETED SUCCESS":
      logging.log(logging.INFO, "ibazel build complete; starting hot reload")
      try:
        reset_runtime()
        execute_main_module()

      except Exception as e:
        runtime().add_loading_error(
          pb.ServerError(exception=str(e), traceback=format_traceback())
        )
        logging.log(
          logging.ERROR, "Could not hot reload due to error:", exc_info=e
        )
      finally:
        hot_reload_finished()


demo_modules = ["demo", "demo.main"]


def main(argv: Sequence[str]):
  flask_app = configure_flask_app(prod_mode=FLAGS.prod)
  if len(FLAGS.path) < 1:
    raise Exception("Required flag 'path'. Received: " + FLAGS.path)

  if not FLAGS.prod:
    enable_debug_mode()

  if FLAGS.reload_demo_modules:
    # If we need to reload demo modules, collect all the modules
    # reference demo/main.py.
    #
    # Because the imports in demo/ do not follow the standard import
    # convention used by the rest of the Bazel workspace, we use
    # a list of the modules stored as a constant in main.py.
    from demo import main

    for section in main.ALL_SECTIONS:
      for example in section.examples:
        demo_modules.append(example.name)

    # Need to reset runtime so that stateclasses registered by demo
    # aren't double-registered when executing the main module.x
    reset_runtime(without_hot_reload=True)
  try:
    execute_main_module()
  except Exception as e:
    # Only record error to runtime if in CI mode.
    if not FLAGS.prod:
      runtime().add_loading_error(
        pb.ServerError(exception=str(e), traceback=format_traceback())
      )
      print("Exception executing module:", e)
    else:
      raise e

  # WARNING: this needs to run *after* the initial `execute_module`
  # has completed, otherwise there's a potential race condition where the
  # background thread and main thread are running `execute_module` which
  # leads to obscure hot reloading bugs.
  if not FLAGS.prod:
    print("Running with hot reload:")
    stdin_thread = threading.Thread(
      target=monitor_stdin, name="mesop_build_watcher_thread"
    )
    stdin_thread.daemon = True
    stdin_thread.start()

  if FLAGS.static_file_runfiles_base:
    static_file_runfiles_base = FLAGS.static_file_runfiles_base
  elif FLAGS.prod:
    static_file_runfiles_base = PROD_PACKAGE_PATH
  else:
    static_file_runfiles_base = EDITOR_PACKAGE_PATH
  configure_static_file_serving(
    flask_app,
    static_file_runfiles_base=static_file_runfiles_base,
    # Keep this palceholder arg; it will be replaced downstream sync.
    livereload_script_url=None,
    # Disabling the gzip cache in editor mode makes developing components
    # much easier.
    disable_gzip_cache=not FLAGS.prod,
  )

  if FLAGS.verbose:
    logging.getLogger("werkzeug").setLevel(logging.INFO)
  else:
    log_startup(port=port())
    logging.getLogger("werkzeug").setLevel(logging.WARN)

  flask_app.run(host=get_public_host(), port=port(), use_reloader=False)


if __name__ == "__main__":
  app.run(main)
