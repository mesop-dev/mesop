"""Proof of concept of a webcomponent wrapper that adds hot key support.

This could be made more reusable if we added on_enter to the text area (but this is
more a hack since typically hot keys use enter+modifier to submit the input) With on
enter, the child text area would get refreshed less, but it would still lose focus,
which is not usable.

Other potential usages:

1. Global app hot keys
2. Close dialogs with escape
"""

from hotkeys_component import HotKey, hotkeys_component

import mesop as me

instruction_text = """
The hotkeys are active when you have focus in the text area.

- Press Escape
- Press Shift+Enter to submit text
- Press CMD+s to save
"""


@me.stateclass
class State:
  input: str
  output: str


def on_load(e: me.LoadEvent):
  me.set_theme_mode("system")


@me.page(
  on_load=on_load,
  path="/hotkeys",
  security_policy=me.SecurityPolicy(
    allowed_iframe_parents=["https://mesop-dev.github.io"],
    allowed_connect_srcs=["https://cdn.jsdelivr.net"],
    allowed_script_srcs=["https://cdn.jsdelivr.net"],
    dangerously_disable_trusted_types=True,
  ),
)
def page():
  state = me.state(State)
  hotkeys = [
    # Ex: Text input submit
    HotKey(key="Enter", modifiers=["shift"], action="submit"),
    # Ex: Custom save override
    HotKey(key="s", modifiers=["meta"], action="save"),
    # Ex: Could be used for closing dialogs
    HotKey(key="Escape", action="close"),
  ]
  with me.box(style=me.Style(margin=me.Margin.all(15))):
    me.text(
      "Hot key example",
      type="headline-4",
      style=me.Style(margin=me.Margin(bottom=5)),
    )
    me.markdown(instruction_text)

    with hotkeys_component(hotkeys=hotkeys, on_hotkey_press=on_key_press):
      me.textarea(
        on_input=on_input, rows=5, style=me.Style(display="block", width="100%")
      )
    with me.box(
      style=me.Style(
        margin=me.Margin(top=15),
        padding=me.Padding.all(10),
      )
    ):
      me.text(state.output)


def on_input(e: me.InputEvent | me.InputEnterEvent):
  state = me.state(State)
  state.input = e.value


def on_key_press(e: me.WebEvent):
  state = me.state(State)

  if e.value["action"] == "submit":
    state.output = "Pressed submit hotkey: " + state.input
  elif e.value["action"] == "save":
    state.output = "Pressed save hotkey."
  elif e.value["action"] == "close":
    state.output = "Pressed close hotkey."
