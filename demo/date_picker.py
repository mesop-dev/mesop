from dataclasses import field
from datetime import date

import mesop as me


@me.stateclass
class State:
  picked_date: date | None = field(default_factory=lambda: date(2024, 10, 1))


def on_load(e: me.LoadEvent):
  me.set_theme_mode("system")


@me.page(
  path="/date_picker",
  security_policy=me.SecurityPolicy(
    allowed_iframe_parents=["https://mesop-dev.github.io"]
  ),
  on_load=on_load,
)
def app():
  state = me.state(State)
  with me.box(
    style=me.Style(
      display="flex",
      flex_direction="column",
      gap=15,
      padding=me.Padding.all(15),
    )
  ):
    me.date_picker(
      label="Date",
      disabled=False,
      placeholder="9/1/2024",
      required=True,
      value=state.picked_date,
      readonly=False,
      hide_required_marker=False,
      color="accent",
      float_label="always",
      appearance="outline",
      on_change=on_date_change,
    )

    me.text("Selected date: " + _render_date(state.picked_date))


def on_date_change(e: me.DatePickerChangeEvent):
  state = me.state(State)
  state.picked_date = e.date


def _render_date(maybe_date: date | None) -> str:
  if maybe_date:
    return maybe_date.strftime("%Y-%m-%d")
  return "None"
