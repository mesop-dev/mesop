from collections.abc import AsyncGenerator, Coroutine
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable, Generator, Type, TypeVar, cast

from flask import g, request

import mesop.protos.ui_pb2 as pb
from mesop.env.env import MESOP_WEBSOCKETS_ENABLED
from mesop.events import LoadEvent, MesopEvent
from mesop.exceptions import MesopDeveloperException, MesopUserException
from mesop.key import Key
from mesop.runtime.context import Context
from mesop.security.security_policy import SecurityPolicy
from mesop.utils.backoff import exponential_backoff
from mesop.warn import warn

Handler = Callable[[Any], None | Generator[None, None, None]]
newline = "\n"


@dataclass
class EmptyState:
  pass


OnLoadHandler = Callable[
  [LoadEvent],
  None
  | Generator[None, None, None]
  | AsyncGenerator[None, None]
  | Coroutine[Any, Any, None],
]


@dataclass(kw_only=True)
class PageConfig:
  page_fn: Callable[[], None]
  title: str
  stylesheets: list[str]
  security_policy: SecurityPolicy
  on_load: OnLoadHandler | None


E = TypeVar("E", bound=MesopEvent)
T = TypeVar("T")


class Runtime:
  def __init__(self):
    self.debug_mode: bool = False
    # If True, then the server is still re-executing the modules
    # needed for hot reloading.
    self.is_hot_reload_in_progress: bool = False
    # Keeps track of the hot reload count so that the server can tell
    # clients polling whether to request a hot reload.
    self.hot_reload_counter = 0
    self._path_to_page_config: dict[str, PageConfig] = {}
    self.component_fns: set[Callable[..., Any]] = set()
    self.event_mappers: dict[Type[Any], Callable[[pb.UserEvent, Key], Any]] = {}
    self._state_classes: list[type[Any]] = []
    self._loading_errors: list[pb.ServerError] = []
    self._has_served_traffic = False
    self._contexts = {}

  def context(self) -> Context:
    if MESOP_WEBSOCKETS_ENABLED and hasattr(request, "websocket_session_id"):
      websocket_session_id = request.websocket_session_id  # type: ignore
      if websocket_session_id not in self._contexts:
        self._contexts[websocket_session_id] = self.create_context()
      return self._contexts[websocket_session_id]
    if "_mesop_context" not in g:
      g._mesop_context = self.create_context()
    return g._mesop_context

  def delete_context(self, websocket_session_id: str) -> None:
    if websocket_session_id in self._contexts:
      del self._contexts[websocket_session_id]
    else:
      warn(
        f"Tried to delete context with websocket_session_id={websocket_session_id} that doesn't exist."
      )

  def create_context(self) -> Context:
    # If running in prod mode, *always* enable the has served traffic safety check.
    # If running in debug mode, *disable* the has served traffic safety check.
    #
    # We don't want to break iterative development where notebook app developers
    # will want to register pages after traffic has been served.
    # Unlike CLI (w/ hot reload), in notebook envs, runtime is *not* reset.
    #
    # For unclear reasons detecting `colab_utils.is_running_ipython` does
    # *not* work here.
    if not self.debug_mode:
      self._has_served_traffic = True
    if len(self._state_classes) == 0:
      states = {EmptyState: EmptyState()}
    else:
      states = {}
      # Create new instances so that we don't accidentally share state across contexts.
      for state_class in self._state_classes:
        states[state_class] = state_class()

    return Context(
      states=cast(dict[Any, Any], states), debug_mode=self.debug_mode
    )

  def wait_for_hot_reload(self):
    # If hot reload is in-progress, the path may not be registered yet because the client reload
    # happened before the server module re-execution completed.
    if self.is_hot_reload_in_progress:
      exponential_backoff(
        lambda: not self.is_hot_reload_in_progress, initial_delay=0.100
      )

  def run_path(self, path: str) -> None:
    if path not in self._path_to_page_config:
      paths = list(self._path_to_page_config.keys())
      if not paths:
        raise MesopDeveloperException(
          """No page has been registered. Read the [page docs](https://mesop-dev.github.io/mesop/api/page/) to configure a page.

If you configured a page, then there was an exception in your code before the page was registered. Check your logs for more details.
          """
        )
      paths.sort()
      raise MesopUserException(
        f"""Accessed path: {path} not registered

Try one of the following paths:
{newline.join([f"[{p}]({p})" for p in paths])}
                                     """
      )
    self._path_to_page_config[path].page_fn()

  def register_page(self, *, path: str, page_config: PageConfig) -> None:
    if self._has_served_traffic:
      raise MesopDeveloperException(
        "Cannot register a page after traffic has been served. You must register all pages upon server startup before any traffic has been served. This prevents security issues."
      )
    self._path_to_page_config[path] = page_config

  def get_page_config(self, *, path: str) -> PageConfig | None:
    return self._path_to_page_config.get(path)

  def get_path_to_page_configs(self) -> dict[str, PageConfig]:
    return deepcopy(self._path_to_page_config)

  def register_state_class(self, state_class: Any) -> None:
    self._state_classes.append(state_class)

  def add_loading_error(self, error: pb.ServerError) -> None:
    """Only put non-context specific errors, because these errors can be potentially shown across contexts."""
    self._loading_errors.append(error)

  def has_loading_errors(self) -> bool:
    return len(self._loading_errors) > 0

  def get_loading_errors(self) -> list[pb.ServerError]:
    return self._loading_errors

  def register_native_component_fn(self, component_fn: Callable[..., Any]):
    self.component_fns.add(component_fn)

  def check_register_web_component_is_valid(self) -> None:
    if self._has_served_traffic:
      raise MesopDeveloperException(
        "Cannot register a web component after traffic has been served. You must define all web components upon server startup before any traffic has been served. This prevents security issues."
      )

  def get_component_fns(self) -> set[Callable[..., Any]]:
    return self.component_fns

  def register_event_mapper(
    self, event: Type[E], map_fn: Callable[[pb.UserEvent, Key], E]
  ):
    self.event_mappers[event] = map_fn

  def get_event_mapper(
    self, event: Type[E]
  ) -> Callable[[pb.UserEvent, Key], E]:
    return self.event_mappers[event]


_runtime = Runtime()


def runtime():
  return _runtime


def reset_runtime(without_hot_reload: bool = False):
  global _runtime
  old_runtime = _runtime
  _runtime = Runtime()
  if not without_hot_reload:
    _runtime.is_hot_reload_in_progress = True
  _runtime.hot_reload_counter = old_runtime.hot_reload_counter
  _runtime.debug_mode = old_runtime.debug_mode
  _runtime.component_fns = old_runtime.component_fns
  _runtime.event_mappers = old_runtime.event_mappers


def enable_debug_mode():
  _runtime.debug_mode = True


def hot_reload_finished():
  _runtime.is_hot_reload_in_progress = False
  _runtime.hot_reload_counter += 1
