import random
from dataclasses import field

from async_action_component import AsyncAction, async_action_component

import mesop as me


@me.stateclass
class State:
  boxes: dict[str, list[bool | int | str]] = field(
    default_factory=lambda: {
      "box1": [False, 0, "red"],
      "box2": [False, 0, "orange"],
      "box3": [False, 0, "yellow"],
    }
  )
  action: str
  duration: int


def on_load(e: me.LoadEvent):
  me.set_theme_mode("system")


@me.page(
  on_load=on_load,
  path="/async_action",
  security_policy=me.SecurityPolicy(
    allowed_iframe_parents=["https://mesop-dev.github.io"],
    allowed_connect_srcs=["https://cdn.jsdelivr.net"],
    allowed_script_srcs=["https://cdn.jsdelivr.net"],
    dangerously_disable_trusted_types=True,
  ),
)
def page():
  state = me.state(State)
  action = (
    AsyncAction(value=state.action, duration_seconds=state.duration)
    if state.action
    else None
  )
  async_action_component(
    action=action, on_started=on_started, on_finished=on_finished
  )
  with me.box(
    style=me.Style(
      display="flex", flex_direction="column", margin=me.Margin.all(15)
    )
  ):
    for key, meta in state.boxes.items():
      with me.box(style=me.Style(padding=me.Padding.all(15))):
        me.button("Show " + key, type="flat", key=key, on_click=on_click)
      if meta[0]:
        with me.box(
          style=me.Style(
            background=str(meta[2]),
            width=100,
            height=100,
            margin=me.Margin(top=15),
            padding=me.Padding.all(15),
          )
        ):
          me.text(f"{meta[0]} {meta[1]}")


def on_click(e: me.ClickEvent):
  state = me.state(State)
  state.action = e.key
  state.duration = random.randint(2, 10)
  state.boxes[e.key][0] = True
  state.boxes[e.key][1] = state.duration


def on_started(e: me.WebEvent):
  state = me.state(State)
  state.action = ""


def on_finished(e: me.WebEvent):
  state = me.state(State)
  state.action = ""
  state.boxes[e.value["action"]][0] = False
