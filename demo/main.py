# Disable import sort ordering due to the hack needed
# to ensure local imports.
# ruff: noqa: E402

import base64
import importlib.util
import inspect
import os
import sys
import types
from dataclasses import dataclass, field
from typing import Literal

import mesop as me

# Append the current directory to sys.path to ensure local imports work
# This is required so mesop/examples/__init__.py can import the modules
# imported below.
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
  sys.path.append(current_dir)


def _import_demo_subdir(demo_name: str) -> types.ModuleType:
  """Load app.py from a demo subdirectory.

  Adds the subdirectory to sys.path so that app.py can import its sibling
  files (e.g. component .py/.js) without needing relative or package-qualified
  imports.
  """
  subdir = os.path.join(current_dir, demo_name)
  if subdir not in sys.path:
    sys.path.append(subdir)
  app_path = os.path.join(subdir, "app.py")
  spec = importlib.util.spec_from_file_location(
    demo_name,
    app_path,
  )
  if spec is None or spec.loader is None:
    raise ImportError(
      f"Could not load demo module '{demo_name}' from {app_path}"
    )
  module = importlib.util.module_from_spec(spec)
  sys.modules[demo_name] = module
  spec.loader.exec_module(module)  # type: ignore[union-attr]
  return module


import glob

import audio as audio
import autocomplete as autocomplete
import badge as badge
import basic_animation as basic_animation
import bootstrap as bootstrap
import box as box
import button as button
import button_toggle as button_toggle
import card as card
import chat as chat
import chat_inputs as chat_inputs
import checkbox as checkbox
import code_demo as code_demo  # cannot call it code due to python library naming conflict
import context_menu as context_menu
import date_picker as date_picker
import date_range_picker as date_range_picker
import density as density
import dialog as dialog
import divider as divider
import embed as embed
import expansion_panel as expansion_panel
import fancy_chat as fancy_chat
import feedback as feedback
import form_billing as form_billing
import form_profile as form_profile
import grid_table as grid_table
import headers as headers
import html_demo as html_demo
import icon as icon
import image as image
import input as input
import link as link
import llm_playground as llm_playground
import llm_rewriter as llm_rewriter
import markdown_demo as markdown_demo  # cannot call it markdown due to python library naming conflict
import markdown_editor as markdown_editor
import plot as plot
import progress_bar as progress_bar
import progress_spinner as progress_spinner
import radio as radio
import select_demo as select_demo  # cannot call it select due to python library naming conflict
import sidenav as sidenav
import slide_toggle as slide_toggle
import slider as slider
import snackbar as snackbar
import tab_group as tab_group
import table as table
import tailwind as tailwind
import text as text
import text_to_image as text_to_image
import text_to_text as text_to_text
import textarea as textarea
import tooltip as tooltip
import uploader as uploader
import video as video

async_action = _import_demo_subdir("async_action")
charts = _import_demo_subdir("charts")
copy_to_clipboard = _import_demo_subdir("copy_to_clipboard")
hotkeys = _import_demo_subdir("hotkeys")
leaflet = _import_demo_subdir("leaflet")
plotly = _import_demo_subdir("plotly")
svg_icon = _import_demo_subdir("svg_icon")


@dataclass
class Example:
  # module_name (should also be the path name)
  name: str
  # Additional files to show in the code viewer (relative to the demo's directory)
  extra_files: list[str] = field(default_factory=list)


@dataclass
class Section:
  name: str
  examples: list[Example]


FIRST_SECTIONS = [
  Section(
    name="Quick start",
    examples=[
      Example(name="chat"),
      Example(name="text_to_image"),
      Example(name="text_to_text"),
    ],
  ),
  Section(
    name="Use cases",
    examples=[
      Example(name="fancy_chat"),
      Example(name="llm_rewriter"),
      Example(name="llm_playground"),
      Example(name="markdown_editor"),
    ],
  ),
  Section(
    name="Patterns",
    examples=[
      Example(name="context_menu"),
      Example(name="dialog"),
      Example(name="grid_table"),
      Example(name="headers"),
      Example(name="snackbar"),
      Example(name="tab_group"),
      Example(name="chat_inputs"),
      Example(name="form_billing"),
      Example(name="form_profile"),
    ],
  ),
  Section(
    name="Features",
    examples=[
      Example(name="density"),
    ],
  ),
  Section(
    name="Misc",
    examples=[
      Example(name="basic_animation"),
      Example(name="feedback"),
    ],
  ),
  Section(
    name="Integrations",
    examples=[
      Example(name="bootstrap"),
      Example(name="tailwind"),
    ],
  ),
]

COMPONENTS_SECTIONS = [
  Section(
    name="Layout",
    examples=[
      Example(name="box"),
      Example(name="sidenav"),
    ],
  ),
  Section(
    name="Text",
    examples=[
      Example(name="text"),
      Example(name="markdown_demo"),
      Example(name="code_demo"),
    ],
  ),
  Section(
    name="Media",
    examples=[
      Example(name="image"),
      Example(name="audio"),
      Example(name="video"),
    ],
  ),
  Section(
    name="Form",
    examples=[
      Example(name="autocomplete"),
      Example(name="button"),
      Example(name="button_toggle"),
      Example(name="checkbox"),
      Example(name="date_picker"),
      Example(name="date_range_picker"),
      Example(name="input"),
      Example(name="textarea"),
      Example(name="radio"),
      Example(name="select_demo"),
      Example(name="slide_toggle"),
      Example(name="slider"),
      Example(name="uploader"),
    ],
  ),
  Section(
    name="Visual",
    examples=[
      Example(name="badge"),
      Example(name="card"),
      Example(name="divider"),
      Example(name="expansion_panel"),
      Example(name="icon"),
      Example(name="progress_bar"),
      Example(name="progress_spinner"),
      Example(name="table"),
      Example(name="tooltip"),
    ],
  ),
  Section(
    name="Web",
    examples=[
      Example(name="embed"),
      Example(name="html_demo"),
      Example(name="link"),
    ],
  ),
  Section(
    name="Web Components",
    examples=[
      Example(
        name="async_action",
        extra_files=[
          "async_action_component.py",
          "async_action_component.js",
        ],
      ),
      Example(
        name="charts",
        extra_files=[
          "chartjs_component.py",
          "chartjs_component.js",
        ],
      ),
      Example(
        name="copy_to_clipboard",
        extra_files=[
          "copy_to_clipboard_component.py",
          "copy_to_clipboard_component.js",
        ],
      ),
      Example(
        name="hotkeys",
        extra_files=[
          "hotkeys_component.py",
          "hotkeys_component.js",
        ],
      ),
      Example(
        name="leaflet",
        extra_files=[
          "leaflet_component.py",
          "leaflet_component.js",
        ],
      ),
      Example(
        name="plotly",
        extra_files=[
          "plotly_component.py",
          "plotly_component.js",
        ],
      ),
      Example(
        name="svg_icon",
        extra_files=[
          "svg_icon_component.py",
          "svg_icon_component.js",
        ],
      ),
    ],
  ),
  Section(
    name="Others",
    examples=[
      Example(name="plot"),
    ],
  ),
]

ALL_SECTIONS = FIRST_SECTIONS + COMPONENTS_SECTIONS

ALL_EXAMPLES: dict[str, Example] = {
  example.name: example
  for section in ALL_SECTIONS
  for example in section.examples
}

BORDER_SIDE = me.BorderSide(
  style="solid",
  width=1,
  color="#dcdcdc",
)


@me.stateclass
class State:
  current_demo: str
  panel_fullscreen: Literal["preview", "editor", None] = None
  # "" on initial load/reset; the main filename (e.g. "app.py") when the user
  # explicitly selects it; or one of the extra_files values otherwise.
  # _get_code_for_example treats any value not in extra_files as the main file.
  selected_file: str = ""


screenshots: dict[str, str] = {}


def load_home_page(e: me.LoadEvent):
  if me.state(ThemeState).dark_mode:
    me.set_theme_mode("dark")
  else:
    me.set_theme_mode("system")
  yield
  screenshot_dir = os.path.join(current_dir, "screenshots")
  screenshot_files = glob.glob(os.path.join(screenshot_dir, "*.webp"))

  for screenshot_file in screenshot_files:
    image_name = os.path.basename(screenshot_file).split(".")[0]
    with open(screenshot_file, "rb") as image_file:
      encoded_string = base64.b64encode(image_file.read()).decode()
      screenshots[image_name] = "data:image/webp;base64," + encoded_string

  yield


@me.page(
  title="Mesop Demos",
  security_policy=me.SecurityPolicy(
    allowed_iframe_parents=["https://mesop-dev.github.io"]
  ),
  on_load=load_home_page,
)
def main_page():
  header()
  with me.box(
    style=me.Style(
      background=me.theme_var("background"),
      flex_grow=1,
      display="flex",
    )
  ):
    if is_desktop():
      side_menu()
    with me.box(
      style=me.Style(
        width="calc(100% - 150px)" if is_desktop() else "100%",
        display="flex",
        gap=24,
        flex_direction="column",
        padding=me.Padding.all(24),
        overflow_y="auto",
      )
    ):
      with me.box(
        style=me.Style(
          height="calc(100vh - 120px)",
        )
      ):
        for section in ALL_SECTIONS:
          with me.box(style=me.Style(margin=me.Margin(bottom=28))):
            me.text(
              section.name,
              style=me.Style(
                font_weight=500,
                font_size=20,
                margin=me.Margin(
                  bottom=16,
                ),
              ),
            )
            with me.box(
              style=me.Style(
                display="flex",
                flex_direction="row",
                flex_wrap="wrap",
                gap=28,
              )
            ):
              for example in section.examples:
                example_card(example.name)


def navigate_example_card(e: me.ClickEvent):
  me.navigate("/embed/" + e.key)


def example_card(name: str):
  with me.box(
    key=name,
    on_click=navigate_example_card,
    style=me.Style(
      border=me.Border.all(
        me.BorderSide(
          width=1,
          color="rgb(220, 220, 220)",
          style="solid",
        )
      ),
      box_shadow="rgba(0, 0, 0, 0.2) 0px 3px 1px -2px, rgba(0, 0, 0, 0.14) 0px 2px 2px, rgba(0, 0, 0, 0.12) 0px 1px 5px",
      cursor="pointer",
      width="min(100%, 150px)",
      border_radius=12,
      background=me.theme_var("background"),
    ),
  ):
    image_url = screenshots.get(name, "")
    me.box(
      style=me.Style(
        background=f'url("{image_url}") center / cover',
        height=112,
        width=150,
      )
    )
    me.text(
      format_example_name(name),
      style=me.Style(
        font_weight=500,
        font_size=18,
        padding=me.Padding.all(12),
        border=me.Border(
          top=me.BorderSide(
            width=1,
            style="solid",
            color="rgb(220, 220, 220)",
          )
        ),
      ),
    )


def on_load_embed(e: me.LoadEvent):
  state = me.state(State)
  if me.state(ThemeState).dark_mode:
    me.set_theme_mode("dark")
  else:
    me.set_theme_mode("system")
  me.set_theme_density(-2)
  if not is_desktop():
    state.panel_fullscreen = "preview"
  state.selected_file = ""


def create_main_fn(example: Example):
  @me.page(
    on_load=on_load_embed,
    title="Mesop Demos",
    path="/embed/" + example.name,
    security_policy=me.SecurityPolicy(
      allowed_iframe_parents=["https://mesop-dev.github.io"]
    ),
  )
  def main():
    with me.box(
      style=me.Style(
        height="100%",
        display="flex",
        flex_direction="column",
        background=me.theme_var("background"),
      )
    ):
      header(demo_name=example.name)
      body(example.name)

  return main


for section in FIRST_SECTIONS + COMPONENTS_SECTIONS:
  for example in section.examples:
    create_main_fn(example)


def body(current_demo: str):
  state = me.state(State)
  with me.box(
    style=me.Style(
      flex_grow=1,
      display="flex",
    )
  ):
    if is_desktop():
      side_menu()
    src = "/" + current_demo
    with me.box(
      style=me.Style(
        width="calc(100% - 150px)" if is_desktop() else "100%",
        display="grid",
        grid_template_columns="1fr 1fr"
        if state.panel_fullscreen is None
        else "1fr",
      )
    ):
      if state.panel_fullscreen != "editor":
        demo_ui(src)
      if state.panel_fullscreen != "preview":
        demo_code(ALL_EXAMPLES[current_demo])


def demo_ui(src: str):
  state = me.state(State)
  with me.box(
    style=me.Style(flex_grow=1),
  ):
    with me.box(
      style=me.Style(
        display="flex",
        justify_content="space-between",
        align_items="center",
        border=me.Border(bottom=BORDER_SIDE),
      )
    ):
      me.text(
        "Preview",
        style=me.Style(
          font_weight=500,
          padding=me.Padding.all(14),
        ),
      )
      if is_desktop():
        with me.tooltip(
          position="above",
          message="Minimize"
          if state.panel_fullscreen == "preview"
          else "Maximize",
        ):
          with me.content_button(type="icon", on_click=toggle_fullscreen):
            me.icon(
              "close_fullscreen"
              if state.panel_fullscreen == "preview"
              else "fullscreen"
            )
      else:
        swap_button()
    me.embed(
      src=src,
      style=me.Style(
        border=me.Border.all(me.BorderSide(width=0)),
        border_radius=2,
        height="calc(100vh - 106px)",
        width="100%",
      ),
    )


def swap_button():
  state = me.state(State)
  with me.tooltip(
    position="above",
    message="Swap for code"
    if state.panel_fullscreen == "preview"
    else "Swap for preview",
  ):
    with me.content_button(type="icon", on_click=swap_fullscreen):
      me.icon("swap_horiz")


def swap_fullscreen(e: me.ClickEvent):
  state = me.state(State)
  if state.panel_fullscreen == "preview":
    state.panel_fullscreen = "editor"
  else:
    state.panel_fullscreen = "preview"


def toggle_fullscreen(e: me.ClickEvent):
  state = me.state(State)
  if state.panel_fullscreen == "preview":
    state.panel_fullscreen = None
  else:
    state.panel_fullscreen = "preview"


_LANG_MAP: dict[str, str] = {
  "py": "python",
  "js": "javascript",
  "ts": "typescript",
  "css": "css",
  "html": "html",
}


def _get_code_for_example(example: Example) -> tuple[str, str]:
  """Returns (source_code, language) for the currently selected file."""
  state = me.state(State)
  module = get_module(example.name)
  if state.selected_file not in example.extra_files:
    return inspect.getsource(module), "python"
  module_dir = os.path.dirname(os.path.abspath(module.__file__))
  path = os.path.abspath(os.path.join(module_dir, state.selected_file))
  # Defense in depth: reject any path that escapes the demo's own directory,
  # even though selected_file is already validated against the extra_files allowlist.
  if not path.startswith(module_dir + os.sep):
    return inspect.getsource(module), "python"
  with open(path, encoding="utf-8") as f:
    code = f.read()
  ext = (
    state.selected_file.rsplit(".", 1)[-1] if "." in state.selected_file else ""
  )
  return code, _LANG_MAP.get(ext, "")


def on_file_select(e: me.SelectSelectionChangeEvent):
  me.state(State).selected_file = e.value


def demo_code(example: Example):
  state = me.state(State)
  module = get_module(example.name)
  main_filename = os.path.basename(module.__file__)
  with me.box(
    style=me.Style(
      flex_grow=1,
      overflow_x="hidden",
      overflow_y="hidden",
      border=me.Border(
        left=BORDER_SIDE,
      ),
      background=me.theme_var("surface-container-low"),
    )
  ):
    with me.box(
      style=me.Style(
        display="flex",
        justify_content="space-between",
        align_items="center",
        border=me.Border(bottom=BORDER_SIDE),
        background=me.theme_var("background"),
      )
    ):
      if example.extra_files:
        effective_value = (
          state.selected_file
          if state.selected_file in example.extra_files
          else main_filename
        )
        with me.box(
          style=me.Style(
            flex_grow=1, overflow_x="hidden", margin=me.Margin(bottom=-21)
          )
        ):
          me.select(
            options=[
              me.SelectOption(label=main_filename, value=main_filename),
              *[
                me.SelectOption(label=os.path.basename(f), value=f)
                for f in example.extra_files
              ],
            ],
            value=effective_value,
            on_selection_change=on_file_select,
            style=me.Style(
              width="100%",
            ),
          )
      else:
        me.text(
          "Code",
          style=me.Style(
            font_weight=500,
            padding=me.Padding.all(14),
          ),
        )
      if not is_desktop():
        swap_button()
    code, lang = _get_code_for_example(example)
    # Use four backticks for code fence to avoid conflicts with backticks being used
    # within the displayed code.
    me.markdown(
      f"````{lang}\n{code}\n````",
      style=me.Style(
        border=me.Border(
          right=BORDER_SIDE,
        ),
        font_size=13,
        height="calc(100vh - 106px)",
        overflow_y="auto",
        width="100%",
      ),
    )


def header(demo_name: str | None = None):
  with me.box(
    style=me.Style(
      border=me.Border(
        bottom=me.BorderSide(
          style="solid",
          width=1,
          color="#dcdcdc",
        )
      ),
      overflow_x="clip",
    )
  ):
    with me.box(
      style=me.Style(
        display="flex",
        align_items="end",
        justify_content="space-between",
        margin=me.Margin(left=12, right=12, bottom=12),
        font_size=24,
      )
    ):
      with me.box(style=me.Style(display="flex")):
        with me.box(
          style=me.Style(display="flex", cursor="pointer"),
          on_click=navigate_home,
        ):
          me.text(
            "Mesop", style=me.Style(font_weight=700, margin=me.Margin(right=8))
          )
          me.text("Demos ")
        if demo_name:
          me.text(
            "— " + format_example_name(demo_name),
            style=me.Style(white_space="nowrap", text_overflow="ellipsis"),
          )
      with me.box(style=me.Style(display="flex", align_items="baseline")):
        with me.box(
          style=me.Style(
            display="flex",
            align_items="baseline",
          ),
        ):
          me.link(
            text="mesop-dev/mesop",
            url="https://github.com/mesop-dev/mesop/",
            open_in_new_tab=True,
            style=me.Style(
              font_size=18,
              color=me.theme_var("primary"),
              text_decoration="none",
              margin=me.Margin(left=8, right=4, bottom=-16, top=-16),
            ),
          )
        me.text(
          "v" + me.__version__,
          style=me.Style(font_size=18, margin=me.Margin(left=16)),
        )
        with me.content_button(
          type="icon",
          style=me.Style(left=8, right=4, top=4),
          on_click=toggle_theme,
        ):
          me.icon(
            "light_mode" if me.theme_brightness() == "dark" else "dark_mode"
          )


@me.stateclass
class ThemeState:
  dark_mode: bool


def toggle_theme(e: me.ClickEvent):
  if me.theme_brightness() == "light":
    me.set_theme_mode("dark")
    me.state(ThemeState).dark_mode = True
  else:
    me.set_theme_mode("light")
    me.state(ThemeState).dark_mode = False


def navigate_home(e: me.ClickEvent):
  me.navigate("/")


def side_menu():
  with me.box(
    style=me.Style(
      padding=me.Padding.all(12),
      width=150,
      flex_grow=0,
      line_height="1.5",
      border=me.Border(right=BORDER_SIDE),
      overflow_x="hidden",
      height="calc(100vh - 60px)",
      overflow_y="auto",
    )
  ):
    for section in FIRST_SECTIONS:
      nav_section(section)
    with me.box(
      style=me.Style(
        margin=me.Margin.symmetric(
          horizontal=-16,
          vertical=16,
        ),
      )
    ):
      me.divider()
    me.text(
      "Components",
      style=me.Style(
        letter_spacing="0.5px",
        margin=me.Margin(bottom=6),
      ),
    )
    for section in COMPONENTS_SECTIONS:
      nav_section(section)


def nav_section(section: Section):
  with me.box(style=me.Style(margin=me.Margin(bottom=12))):
    me.text(section.name, style=me.Style(font_weight=700))
    for example in section.examples:
      example_name = format_example_name(example.name)
      path = f"/embed/{example.name}"
      with me.box(
        style=me.Style(color=me.theme_var("primary"), cursor="pointer"),
        on_click=set_demo,
        key=path,
      ):
        me.text(example_name)


def set_demo(e: me.ClickEvent):
  me.navigate(e.key)


def format_example_name(name: str):
  return (
    (" ".join(name.split("_")))
    .capitalize()
    .replace("Llm", "LLM")
    .replace(" demo", "")
  )


def get_module(module_name: str):
  if module_name in globals():
    return globals()[module_name]
  raise me.MesopDeveloperException(f"Module {module_name} not supported")


def is_desktop():
  return me.viewport_size().width > 760
