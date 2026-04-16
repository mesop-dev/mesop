import sys
import types
from collections.abc import Callable
from typing import Any, TypeVar, cast

from mesop.colab.colab_run import colab_run as colab_run
from mesop.colab.colab_show import colab_show as colab_show
from mesop.commands.cookie_class import cookie as cookie
from mesop.commands.cookie_class import cookieclass as cookieclass
from mesop.commands.focus_component import focus_component as focus_component
from mesop.commands.navigate import navigate as navigate
from mesop.commands.scroll_into_view import scroll_into_view as scroll_into_view
from mesop.commands.set_cookie import delete_cookie as delete_cookie
from mesop.commands.set_cookie import set_cookie as set_cookie
from mesop.commands.set_page_title import (
  set_page_title as set_page_title,
)
from mesop.component_helpers import (
  Border as Border,
)
from mesop.component_helpers import (
  BorderSide as BorderSide,
)
from mesop.component_helpers import (
  Margin as Margin,
)
from mesop.component_helpers import (
  Padding as Padding,
)
from mesop.component_helpers import (
  Style as Style,
)
from mesop.component_helpers.helper import (
  NamedSlot as NamedSlot,
)
from mesop.component_helpers.helper import (
  component as component,
)
from mesop.component_helpers.helper import (
  content_component as content_component,
)
from mesop.component_helpers.helper import (
  insert_web_component as insert_web_component,
)
from mesop.component_helpers.helper import (
  slot as slot,
)
from mesop.component_helpers.helper import (
  slotclass as slotclass,
)
from mesop.component_helpers.web_component import (
  web_component as web_component,
)
from mesop.components.accordion.accordion import accordion as accordion
from mesop.components.audio.audio import audio as audio
from mesop.components.autocomplete.autocomplete import (
  AutocompleteEnterEvent as AutocompleteEnterEvent,
)
from mesop.components.autocomplete.autocomplete import (
  AutocompleteOption as AutocompleteOption,
)
from mesop.components.autocomplete.autocomplete import (
  AutocompleteOptionGroup as AutocompleteOptionGroup,
)
from mesop.components.autocomplete.autocomplete import (
  AutocompleteSelectionChangeEvent as AutocompleteSelectionChangeEvent,
)
from mesop.components.autocomplete.autocomplete import (
  autocomplete as autocomplete,
)
from mesop.components.badge.badge import badge as badge

# REF(//scripts/scaffold_component.py):insert_component_import_export
from mesop.components.box.box import box as box
from mesop.components.button.button import (
  button as button,
)
from mesop.components.button.button import (
  content_button as content_button,
)
from mesop.components.button_toggle.button_toggle import (
  ButtonToggleButton as ButtonToggleButton,
)
from mesop.components.button_toggle.button_toggle import (
  ButtonToggleChangeEvent as ButtonToggleChangeEvent,
)
from mesop.components.button_toggle.button_toggle import (
  button_toggle as button_toggle,
)
from mesop.components.card.card import card as card
from mesop.components.card_actions.card_actions import (
  card_actions as card_actions,
)
from mesop.components.card_content.card_content import (
  card_content as card_content,
)
from mesop.components.card_header.card_header import card_header as card_header
from mesop.components.checkbox.checkbox import (
  CheckboxChangeEvent as CheckboxChangeEvent,
)
from mesop.components.checkbox.checkbox import (
  CheckboxIndeterminateChangeEvent as CheckboxIndeterminateChangeEvent,
)
from mesop.components.checkbox.checkbox import (
  checkbox as checkbox,
)
from mesop.components.checkbox.checkbox import (
  content_checkbox as content_checkbox,
)
from mesop.components.code.code import code as code
from mesop.components.date_range_picker.date_range_picker import (
  DateRangePickerChangeEvent as DateRangePickerChangeEvent,
)
from mesop.components.date_range_picker.date_range_picker import (
  date_range_picker as date_range_picker,
)
from mesop.components.datepicker.datepicker import (
  DatePickerChangeEvent as DatePickerChangeEvent,
)
from mesop.components.datepicker.datepicker import date_picker as date_picker
from mesop.components.divider.divider import divider as divider
from mesop.components.embed.embed import embed as embed
from mesop.components.expansion_panel.expansion_panel import (
  ExpansionPanelToggleEvent as ExpansionPanelToggleEvent,
)
from mesop.components.expansion_panel.expansion_panel import (
  expansion_panel as expansion_panel,
)
from mesop.components.html.html import html as html
from mesop.components.icon.icon import icon as icon
from mesop.components.image.image import image as image
from mesop.components.input.input import EnterEvent as EnterEvent
from mesop.components.input.input import InputBlurEvent as InputBlurEvent
from mesop.components.input.input import InputEnterEvent as InputEnterEvent
from mesop.components.input.input import Shortcut as Shortcut
from mesop.components.input.input import (
  TextareaShortcutEvent as TextareaShortcutEvent,
)
from mesop.components.input.input import input as input
from mesop.components.input.input import native_textarea as native_textarea
from mesop.components.input.input import textarea as textarea
from mesop.components.link.link import link as link
from mesop.components.markdown.markdown import markdown as markdown
from mesop.components.plot.plot import (
  plot as plot,
)
from mesop.components.progress_bar.progress_bar import (
  ProgressBarAnimationEndEvent as ProgressBarAnimationEndEvent,
)
from mesop.components.progress_bar.progress_bar import (
  progress_bar as progress_bar,
)
from mesop.components.progress_spinner.progress_spinner import (
  progress_spinner as progress_spinner,
)
from mesop.components.radio.radio import (
  RadioChangeEvent as RadioChangeEvent,
)
from mesop.components.radio.radio import (
  RadioOption as RadioOption,
)
from mesop.components.radio.radio import (
  radio as radio,
)
from mesop.components.select.select import (
  SelectOpenedChangeEvent as SelectOpenedChangeEvent,
)
from mesop.components.select.select import (
  SelectOption as SelectOption,
)
from mesop.components.select.select import (
  SelectSelectionChangeEvent as SelectSelectionChangeEvent,
)
from mesop.components.select.select import (
  select as select,
)
from mesop.components.sidenav.sidenav import (
  SidenavOpenedChangedEvent as SidenavOpenedChangedEvent,
)
from mesop.components.sidenav.sidenav import sidenav as sidenav
from mesop.components.slide_toggle.slide_toggle import (
  SlideToggleChangeEvent as SlideToggleChangeEvent,
)
from mesop.components.slide_toggle.slide_toggle import (
  content_slide_toggle as content_slide_toggle,
)
from mesop.components.slide_toggle.slide_toggle import (
  slide_toggle as slide_toggle,
)
from mesop.components.slider.slider import (
  SliderValueChangeEvent as SliderValueChangeEvent,
)
from mesop.components.slider.slider import (
  slider as slider,
)
from mesop.components.table.table import (
  TableClickEvent as TableClickEvent,
)
from mesop.components.table.table import (
  TableColumn as TableColumn,
)
from mesop.components.table.table import (
  TableHeader as TableHeader,
)
from mesop.components.table.table import table as table
from mesop.components.text.text import text as text
from mesop.components.tooltip.tooltip import tooltip as tooltip
from mesop.components.uploader.uploader import (
  UploadedFile as UploadedFile,
)
from mesop.components.uploader.uploader import (
  UploadEvent as UploadEvent,
)
from mesop.components.uploader.uploader import (
  content_uploader as content_uploader,
)
from mesop.components.uploader.uploader import uploader as uploader
from mesop.components.video.video import video as video
from mesop.dataclass_utils import dataclass_with_defaults
from mesop.events import (
  ClickEvent as ClickEvent,
)
from mesop.events import (
  InputEvent as InputEvent,
)
from mesop.events import (
  LoadEvent as LoadEvent,
)
from mesop.events import (
  RightClickEvent as RightClickEvent,
)
from mesop.events import WebEvent as WebEvent
from mesop.exceptions import (
  MesopDeveloperException as MesopDeveloperException,
)
from mesop.exceptions import (
  MesopException as MesopException,
)
from mesop.exceptions import (
  MesopInternalException as MesopInternalException,
)
from mesop.exceptions import (
  MesopUserException as MesopUserException,
)
from mesop.features import page as page
from mesop.features.query_params import query_params as query_params
from mesop.features.theme import set_theme_density as set_theme_density
from mesop.features.theme import set_theme_mode as set_theme_mode
from mesop.features.theme import theme_brightness as theme_brightness
from mesop.features.theme import theme_var as theme_var
from mesop.features.viewport_size import Size as Size
from mesop.features.viewport_size import viewport_size as viewport_size
from mesop.key import Key as Key
from mesop.runtime import runtime
from mesop.security.security_policy import SecurityPolicy as SecurityPolicy
from mesop.server.wsgi_app import create_wsgi_app as create_wsgi_app
from mesop.version import VERSION

__version__ = VERSION

_wsgi_app = create_wsgi_app(debug_mode=False)


class _WsgiAppModule(types.ModuleType):
  def __call__(
    self, environ: dict[Any, Any], start_response: Callable[..., Any]
  ):
    return _wsgi_app(environ, start_response)


sys.modules[__name__].__class__ = _WsgiAppModule

_T = TypeVar("_T")


def state(state: type[_T]) -> _T:
  return runtime().context().state(state)


def stateclass(cls: type[_T] | None, **kw_args: Any) -> type[_T]:
  """
  Similar as dataclass, but it also registers with Mesop runtime().
  """

  def wrapper(cls: type[_T]) -> type[_T]:
    dataclass_cls = dataclass_with_defaults(cls, **kw_args)
    runtime().register_state_class(dataclass_cls)
    return dataclass_cls

  if cls is None:
    # too difficult to properly type annotate
    anyWrapper = cast(Any, wrapper)
    # We're called with parens.
    return anyWrapper

  return wrapper(cls)
