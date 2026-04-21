from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Literal

import mesop as me


@dataclass
class HotKey:
  key: str
  action: str
  modifiers: list[Literal["ctrl", "alt", "shift", "meta"]] = field(
    default_factory=list
  )


@me.web_component(path="./hotkeys_component.js")
def hotkeys_component(
  *,
  hotkeys: list[HotKey],
  on_hotkey_press: Callable[[me.WebEvent], Any],
  key: str | None = None,
):
  return me.insert_web_component(
    name="hotkeys-component",
    key=key,
    events={
      "keyPressEvent": on_hotkey_press,
    },
    # Unable to serialize dataclass, so converting to dict.
    properties={"hotkeys": [asdict(hotkey) for hotkey in hotkeys]},
  )
