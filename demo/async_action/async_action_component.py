from dataclasses import asdict, dataclass
from typing import Any, Callable

import mesop as me


@dataclass
class AsyncAction:
  value: str
  duration_seconds: int


@me.web_component(path="./async_action_component.js")
def async_action_component(
  *,
  on_started: Callable[[me.WebEvent], Any],
  on_finished: Callable[[me.WebEvent], Any],
  action: AsyncAction | None = None,
  key: str | None = None,
):
  """Creates an invisibe component that will delay state changes asynchronously.

  Right now this implementation is limited since we basically just pass the key around.
  But ideally we also pass in some kind of value to update when the time out expires.

  The main benefit of this component is for cases, such as status messages that may
  appear and disappear after some duration. The primary example here is the example
  snackbar widget, which right now blocks the UI when using the sleep yield approach.

  The other benefit of this component is that it works generically (rather than say
  implementing a custom snackbar widget as a web component).
  """
  return me.insert_web_component(
    name="async-action-component",
    key=key,
    events={
      "startedEvent": on_started,
      "finishedEvent": on_finished,
    },
    properties={"action": asdict(action) if action else ""},
  )
