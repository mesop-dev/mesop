import logging
import os
import sys
from typing import Sequence

from absl import app, flags

from mesop.runtime import enable_debug_mode
from mesop.server.hot_reload import execute_main_module, start_file_watcher
from mesop.server.wsgi_app import create_app

FLAGS = flags.FLAGS

flags.DEFINE_bool(
  "prod", False, "set to true for prod mode; otherwise editor mode."
)


def main(argv: Sequence[str]):
  if len(argv) < 2:
    print(
      """\u001b[31mERROR: missing command-line argument to Mesop.\u001b[0m

Example run command:
$\u001b[35m mesop file.py\u001b[0m"""
    )
    sys.exit(1)

  if argv[1] == "init":
    if len(argv) > 3:
      print(
        f"""\u001b[31mERROR: Too many command-line arguments for mesop init.\u001b[0m

Actual:
$\u001b[35m mesop {" ".join(argv[1:])}\u001b[0m

Re-run with:
$\u001b[35m mesop init file.py\u001b[0m"""
      )
      sys.exit(1)

    filename = argv[2] if len(argv) == 3 else "main.py"
    absolute_path = make_path_absolute(filename)
    if os.path.isfile(absolute_path):
      print(f"\u001b[31mERROR: {filename} already exists.\u001b[0m")
      sys.exit(1)
    with open(
      os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "../examples/starter_kit/starter_kit.py",
      )
    ) as src_file:
      with open(absolute_path, "w") as dest_file:
        dest_file.write(src_file.read().replace("/starter_kit", "/"))
    print(f"""Created starter kit Mesop app at {filename} 🎉

Run Mesop app:
$\u001b[35m mesop {filename}\u001b[0m
""")
    sys.exit(0)
  if len(argv) > 2:
    print(
      f"""\u001b[31mERROR: Too many command-line arguments.\u001b[0m

Actual:
$\u001b[35m mesop {" ".join(argv[1:])}\u001b[0m

Re-run with:
$\u001b[35m mesop {argv[1]}\u001b[0m"""
    )
    sys.exit(1)

  if not FLAGS.prod:
    enable_debug_mode()

  absolute_path = make_path_absolute(argv[1])

  # If you run `$ python /path/to/script.py`, Python will add
  # "/path/to" to sys.path.
  #
  # Running `$ mesop /path/to/script.py` should mimic this behavior
  # so that imports work as expected (e.g. https://github.com/mesop-dev/mesop/issues/128)
  #
  # Ref:
  # https://docs.python.org/3/library/sys_path_init.html
  sys.path = [os.path.dirname(absolute_path), *sys.path]

  app = create_app(
    prod_mode=FLAGS.prod,
    run_block=lambda: execute_main_module(
      absolute_path=absolute_path, prod_mode=FLAGS.prod
    ),
  )

  # WARNING: this needs to run *after* the initial `execute_module`
  # has completed, otherwise there's a potential race condition where the
  # background thread and main thread are running `execute_module` which
  # leads to obscure hot reloading bugs.
  if not FLAGS.prod:
    print("Running with hot reload:")
    start_file_watcher(absolute_path, prod_mode=False)

  logging.getLogger("werkzeug").setLevel(logging.WARN)
  app.run()


def make_path_absolute(file_path: str):
  if os.path.isabs(file_path):
    return file_path
  # Otherwise, make the relative path absolute by joining
  # with current working dir.
  absolute_path = os.path.join(os.getcwd(), file_path)
  return absolute_path


def run_main():
  app.run(main)


if __name__ == "__main__":
  run_main()
