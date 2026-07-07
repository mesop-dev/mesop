import threading

from absl import flags

from mesop.runtime import enable_debug_mode
from mesop.server.constants import EDITOR_PACKAGE_PATH, PROD_PACKAGE_PATH
from mesop.server.logging import log_startup
from mesop.server.server import configure_flask_app
from mesop.server.static_file_serving import configure_static_file_serving
from mesop.utils import colab_utils
from mesop.utils.host_util import get_public_host


def colab_run(*, port: int = 32123, prod_mode: bool = False):
  """
  When running in Colab environment, this will launch the web server.

  Otherwise, this is a no-op.
  """
  if not colab_utils.is_running_in_colab():
    print("Not running Colab: `colab_run` is a no-op")
    return
  notebook_run(port=port, prod_mode=prod_mode)


def notebook_run(*, port: int = 32123, prod_mode: bool = False):
  """
  When running in a notebook environment, this will launch the web server.

  Otherwise, this is a no-op.

  Use this for non-Colab notebook environments like Jupyter/JupyterLab.
  """
  if not colab_utils.is_running_ipython():
    print("Not running in a notebook environment: `notebook_run` is a no-op")
    return
  # Ensures the flags are marked as parsed before creating the app otherwise you will
  # get UnparsedFlagAccessError.
  #
  # Depending on the Colab environment, the flags may or may not be parsed.
  #
  # Note: this ignore all Mesop CLI flags, but we could provide a way to override
  # Mesop defined flags in the future if necessary.
  if not flags.FLAGS.is_parsed():
    flags.FLAGS.mark_as_parsed()
  flask_app = configure_flask_app(prod_mode=prod_mode)
  if not prod_mode:
    enable_debug_mode()

  configure_static_file_serving(
    flask_app,
    static_file_runfiles_base=PROD_PACKAGE_PATH
    if prod_mode
    else EDITOR_PACKAGE_PATH,
  )

  log_startup(port=port)

  def run_flask_app():
    flask_app.run(host=get_public_host(), port=port, use_reloader=False)

  # Launch Flask in background thread so we don't hog up the main thread
  # for regular Colab usage.
  threading.Thread(target=run_flask_app).start()
