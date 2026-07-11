import time

from flask import Flask, Response, request

from mesop.runtime import runtime
from mesop.server.server_utils import prefix_base_url

# Cap how long a single poll can block so that a request can't tie up a
# server thread/connection indefinitely when no hot reload ever happens
# during its lifetime. The client detects an unchanged counter and simply
# polls again.
_MAX_POLL_SECONDS = 25


def configure_debug_routes(flask_app: Flask):
  @flask_app.route(prefix_base_url("/__hot-reload__"))
  def hot_reload() -> Response:
    counter = int(request.args["counter"])
    start_time = time.monotonic()
    while counter >= runtime().hot_reload_counter:
      if time.monotonic() - start_time > _MAX_POLL_SECONDS:
        break
      # Sleep a short duration but not too short that we hog up excessive CPU.
      time.sleep(0.1)
    response = Response(str(runtime().hot_reload_counter), status=200)
    return response
