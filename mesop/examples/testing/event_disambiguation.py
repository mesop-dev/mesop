"""
Example demonstrating the event disambiguation fix.

This example shows that the same handler function can now be used
with different event types (blur and selection change) without conflicts.

Bug: https://github.com/mesop-dev/mesop/issues/1319
"""

import mesop as me


@me.stateclass
class State:
  input_value: str = ""
  select_value: str = ""
  events_received: list[str]


def shared_handler(event):
  """Handler that can handle both InputBlurEvent and SelectSelectionChangeEvent."""
  state = me.state(State)

  # Check event type and handle accordingly
  if isinstance(event, me.InputBlurEvent):
    state.input_value = event.value
    state.events_received.append(f"Blur event: {event.value}")
  elif isinstance(event, me.SelectSelectionChangeEvent):
    state.select_value = event.value
    state.events_received.append(f"Select event: {event.value}")


@me.page(path="/test_event_disambiguation")
def page():
  state = me.state(State)

  me.text("Event Disambiguation Test", type="headline-5")

  # Use the same handler for both input blur and select change
  me.input(
    label="Input",
    on_blur=shared_handler,
  )

  me.select(
    label="Select",
    options=[
      me.SelectOption(label="Option 1", value="opt1"),
      me.SelectOption(label="Option 2", value="opt2"),
      me.SelectOption(label="Option 3", value="opt3"),
    ],
    on_selection_change=shared_handler,
  )

  me.text(f"Input value: {state.input_value}")
  me.text(f"Select value: {state.select_value}")

  me.text("Events received:", type="headline-6")
  for event_msg in state.events_received:
    me.text(f"- {event_msg}")
