import logging
import os
import sys
import threading
import time
from typing import cast

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

import mesop.protos.ui_pb2 as pb
from mesop.cli.execute_module import execute_module, get_module_name_from_path
from mesop.exceptions import format_traceback
from mesop.runtime import hot_reload_finished, reset_runtime, runtime

app_modules: set[str] = set()


def clear_app_modules() -> None:
  # Remove labs modules because they function as application code
  # and they need to be re-executed so that their stateclass is
  # re-registered because the runtime is reset.
  labs_modules: set[str] = set()
  for module in sys.modules:
    if module.startswith("mesop.labs"):
      labs_modules.add(module)
  for module in labs_modules:
    del sys.modules[module]

  for module in app_modules:
    if module in sys.modules:
      del sys.modules[module]


def add_app_module(workspace_dir_path: str, app_module_path: str) -> None:
  module_name = get_app_module_name(
    workspace_dir_path=workspace_dir_path, app_module_path=app_module_path
  )
  app_modules.add(module_name)


def remove_app_module(workspace_dir_path: str, app_module_path: str) -> None:
  module_name = get_app_module_name(
    workspace_dir_path=workspace_dir_path, app_module_path=app_module_path
  )
  app_modules.discard(module_name)


def get_app_module_name(workspace_dir_path: str, app_module_path: str) -> str:
  relative_path = os.path.relpath(app_module_path, workspace_dir_path)

  return (
    relative_path.replace(os.sep, ".")
    # Special case __init__.py:
    # e.g. foo.bar.__init__.py -> foo.bar
    # Otherwise, remove the ".py" suffix
    .removesuffix(".__init__.py")
    .removesuffix(".py")
  )


class ReloadEventHandler(FileSystemEventHandler):
  def __init__(
    self, absolute_path: str, workspace_dir_path: str, prod_mode: bool = False
  ):
    self.count = 0
    self.absolute_path = absolute_path
    self.workspace_dir_path = workspace_dir_path
    self.prod_mode = prod_mode

  def on_modified(self, event: FileSystemEvent):
    src_path = cast(str, event.src_path)
    # This could potentially over-trigger if .py files which are
    # not application modules are modified (e.g. in venv directories)
    # but this should be rare.
    if src_path.endswith(".py"):
      try:
        self.count += 1
        print(f"Hot reload #{self.count}: starting...")
        reset_runtime()
        execute_main_module(
          absolute_path=self.absolute_path, prod_mode=self.prod_mode
        )
        hot_reload_finished()
        print(f"Hot reload #{self.count}: finished!")
      except Exception as e:
        logging.log(
          logging.ERROR, "Could not hot reload due to error:", exc_info=e
        )

  def on_created(self, event: FileSystemEvent):
    src_path = cast(str, event.src_path)
    if src_path.endswith(".py"):
      print(f"Watching new Python module: {event.src_path}")
      add_app_module(
        workspace_dir_path=self.workspace_dir_path,
        app_module_path=event.src_path,
      )

  def on_deleted(self, event: FileSystemEvent):
    src_path = cast(str, event.src_path)
    if src_path.endswith(".py"):
      print(f"Stopped watching deleted Python module: {event.src_path}")
      remove_app_module(
        workspace_dir_path=self.workspace_dir_path,
        app_module_path=event.src_path,
      )


def fs_watcher(absolute_path: str, prod_mode: bool = False):
  """
  Filesystem watcher using watchdog. Watches for any changes in the specified directory
  and triggers hot reload on change.
  """
  workspace_dir_path = os.path.dirname(absolute_path)
  # Initially track all the files on the file system and then rely on watchdog.
  for root, dirnames, files in os.walk(workspace_dir_path):
    # Filter out unusual directories, e.g. starting with "." because they
    # can be special directories, because venv directories
    # can have lots of Python files that are not application Python modules.
    new_dirnames: list[str] = []
    for d in dirnames:
      if d.startswith("."):
        continue
      if d == "__pycache__":
        continue
      if d == "venv":
        continue
      new_dirnames.append(d)

    dirnames[:] = new_dirnames

    for file in files:
      if file.endswith(".py"):
        full_path = os.path.join(root, file)
        relative_path = os.path.relpath(full_path, workspace_dir_path)
        add_app_module(
          workspace_dir_path=workspace_dir_path, app_module_path=relative_path
        )

  event_handler = ReloadEventHandler(
    absolute_path=absolute_path,
    workspace_dir_path=workspace_dir_path,
    prod_mode=prod_mode,
  )
  observer = Observer()
  observer.schedule(event_handler, path=workspace_dir_path, recursive=True)  # type: ignore
  observer.start()
  try:
    while True:
      time.sleep(0.1)
  except KeyboardInterrupt:
    observer.stop()
  observer.join()


def execute_main_module(absolute_path: str, prod_mode: bool = False):
  try:
    clear_app_modules()
    execute_module(
      module_path=absolute_path,
      module_name=get_module_name_from_path(absolute_path),
    )
  except Exception as e:
    if not prod_mode:
      runtime().add_loading_error(
        pb.ServerError(exception=str(e), traceback=format_traceback())
      )
    raise e


def start_file_watcher(absolute_path: str, prod_mode: bool = False) -> None:
  """
  Starts a background daemon thread that watches for file changes and
  triggers hot reload. Safe to call multiple times — only starts once.
  """
  thread = threading.Thread(
    target=lambda: fs_watcher(absolute_path, prod_mode=prod_mode),
    name="mesop_fs_watcher_thread",
  )
  thread.daemon = True
  thread.start()
