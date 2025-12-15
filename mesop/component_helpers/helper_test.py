from typing import Callable
from unittest.mock import patch

import pytest
from flask import Flask

import mesop.protos.ui_pb2 as pb
from mesop.component_helpers.helper import (
  DetachedNodeTreeStateContext,
  NamedSlot,
  UnnamedSlot,
  _UserCompositeComponent,
  check_property_keys_is_safe,
  register_event_handler,
  slot,
  slotclass,
)
from mesop.events import InputEvent, MesopEvent
from mesop.exceptions import MesopDeveloperException
from mesop.key import Key
from mesop.runtime.context import NodeTreeState
from mesop.runtime.runtime import Runtime


def create_default_single_component():
  return pb.Component(
    key=pb.Key(key="key"),
    style=pb.Style(color="red", columns="1"),
    style_debug_json="debug json string",
    type=pb.Type(
      name=pb.ComponentName(core_module=True, fn_name="test"), value=b"value"
    ),
    source_code_location=pb.SourceCodeLocation(module="x", line=1, col=2),
  )


def add_child(runtime: Callable[[], Runtime], component: pb.Component):
  runtime().context().current_node().children.add().CopyFrom(component)


def test_check_property_keys_is_safe_raises_exception():
  with pytest.raises(MesopDeveloperException):
    check_property_keys_is_safe({"src": None}.keys())
  with pytest.raises(MesopDeveloperException):
    check_property_keys_is_safe({"SRC": None}.keys())

  with pytest.raises(MesopDeveloperException):
    check_property_keys_is_safe({"srcdoc": None}.keys())

  with pytest.raises(MesopDeveloperException):
    check_property_keys_is_safe({"on": None}.keys())
  with pytest.raises(MesopDeveloperException):
    check_property_keys_is_safe({"On": None}.keys())
  with pytest.raises(MesopDeveloperException):
    check_property_keys_is_safe({"ON": None}.keys())
  with pytest.raises(MesopDeveloperException):
    check_property_keys_is_safe({"onClick": None}.keys())


def test_check_property_keys_is_safe_passes():
  check_property_keys_is_safe({"a": None}.keys())
  check_property_keys_is_safe({"decrement": None}.keys())
  check_property_keys_is_safe({"click-on": None}.keys())


@pytest.fixture
def app():
  app = Flask(__name__)
  return app


@pytest.fixture
@patch("mesop.component_helpers.helper.runtime")
def runtime(mock_runtime):
  mock_runtime.return_value = Runtime()
  return mock_runtime


@slotclass
class TestSlot:
  a: NamedSlot
  b: NamedSlot


def test_slotclass_init():
  TestSlot(
    a=NamedSlot(NodeTreeState(), "a"),  # type: ignore
    b=NamedSlot(NodeTreeState(), "b"),  # type: ignore
  )


def test_slotclass_init_empty_positional_args_raises_type_error():
  with pytest.raises(TypeError):
    TestSlot(
      NamedSlot(NodeTreeState(), "a"),  # type: ignore
      NamedSlot(NodeTreeState(), "b"),
    )


def test_slotclass_init_empty_raises_type_error():
  with pytest.raises(TypeError):
    TestSlot()


def test_slotclass_fields_must_be_NamedSlot_class():
  with pytest.raises(MesopDeveloperException):

    @slotclass
    class TestSlotBadFieldType:
      a: NamedSlot
      b: str


@pytest.mark.usefixtures("runtime")
def test_named_slot_multiple_calls_raises_dev_exception(app):
  with app.app_context():
    detached_node_tree_state = NodeTreeState()
    named_slot = NamedSlot(detached_node_tree_state, name="test")
    named_slot()

    with pytest.raises(MesopDeveloperException):
      named_slot()


def test_detached_node_tree_state_context(runtime, app):
  with app.app_context():
    node_tree_state = runtime().context().get_node_tree_state()
    detached_node_tree_state = NodeTreeState()
    c1 = create_default_single_component()
    detached_node_tree_state.set_current_node(c1)

    with DetachedNodeTreeStateContext(detached_node_tree_state):
      assert (
        runtime().context().get_node_tree_state() == detached_node_tree_state
      )

    assert runtime().context().get_node_tree_state() == node_tree_state


def test_user_composite_component_unnamed(runtime, app):
  with app.app_context():
    c1 = create_default_single_component()
    c2 = create_default_single_component()
    c3 = create_default_single_component()
    c3.style.CopyFrom(pb.Style(color="blue"))

    def unnamed_component():
      add_child(runtime, c1)
      slot()
      add_child(runtime, c2)

    with _UserCompositeComponent(
      unnamed_component, named_slots_cls=UnnamedSlot
    ):
      add_child(runtime, c3)

    assert runtime().context().current_node().children[1] == c3


@pytest.mark.usefixtures("runtime")
def test_user_composite_component_unnamed_no_slot(app):
  with app.app_context():

    def unnamed_component_no_slots():
      pass

    with pytest.raises(
      MesopDeveloperException,
      match="Must configure one child slot",
    ):
      _UserCompositeComponent(
        unnamed_component_no_slots, named_slots_cls=UnnamedSlot
      )


@pytest.mark.usefixtures("runtime")
def test_user_composite_component_unnamed_cannot_contain_named_slots(app):
  with app.app_context():

    def unnamed_component_with_named_slots():
      slot("test")

    with pytest.raises(
      MesopDeveloperException,
      match="Named slots are not allowed",
    ):
      _UserCompositeComponent(
        unnamed_component_with_named_slots, named_slots_cls=UnnamedSlot
      )


@pytest.mark.usefixtures("runtime")
def test_user_composite_component_named_duplicate_slot_names(app):
  with app.app_context():

    def named_component_with_duplicates():
      slot("a")
      slot("a")

    with pytest.raises(
      MesopDeveloperException,
      match="Multiple slots of the same",
    ):
      _UserCompositeComponent(
        named_component_with_duplicates, named_slots_cls=TestSlot
      )


@pytest.mark.usefixtures("runtime")
def test_user_composite_component_named_with_unnamed_slots(app):
  with app.app_context():

    def named_component_with_unnamed_slot():
      slot("a")
      slot()

    with pytest.raises(
      TypeError,
      match="unexpected keyword argument ''",
    ):
      _UserCompositeComponent(
        named_component_with_unnamed_slot, named_slots_cls=TestSlot
      )


def test_user_composite_component_named(runtime, app):
  with app.app_context():
    c1 = create_default_single_component()
    c2 = create_default_single_component()
    c3 = create_default_single_component()
    c3.style.CopyFrom(pb.Style(color="blue"))
    c4 = create_default_single_component()
    c4.style.CopyFrom(pb.Style(color="green"))

    def named_component():
      add_child(runtime, c1)
      slot("b")
      add_child(runtime, c2)
      slot("a")

    with _UserCompositeComponent(
      named_component, named_slots_cls=TestSlot
    ) as c:
      with c.a():
        add_child(runtime, c3)

      with c.b():
        add_child(runtime, c4)

    assert runtime().context().current_node().children[1] == c4
    assert runtime().context().current_node().children[3] == c3


@pytest.mark.usefixtures("runtime")
def test_user_composite_component_named_slot_not_used(runtime, app):
  with app.app_context():
    c1 = create_default_single_component()
    c2 = create_default_single_component()
    c3 = create_default_single_component()
    c3.style.CopyFrom(pb.Style(color="blue"))
    c4 = create_default_single_component()
    c4.style.CopyFrom(pb.Style(color="green"))

    def named_component():
      add_child(runtime, c1)
      slot("b")
      add_child(runtime, c2)
      slot("a")

    with pytest.raises(
      MesopDeveloperException,
      match="Content for named slot 'b' was not set.",
    ):
      with _UserCompositeComponent(
        named_component, named_slots_cls=TestSlot
      ) as c:
        with c.a():
          add_child(runtime, c3)


@pytest.mark.usefixtures("runtime")
def test_user_composite_component_named_with_missing_slot(app):
  with app.app_context():

    def named_component_with_missing_slot():
      slot("a")

    with pytest.raises(
      TypeError,
      match="required keyword-only argument: 'b'",
    ):
      _UserCompositeComponent(
        named_component_with_missing_slot, named_slots_cls=TestSlot
      )


@pytest.mark.usefixtures("runtime")
def test_user_composite_component_named_with_extra_named_slot(app):
  with app.app_context():

    def named_component_with_missing_slot():
      slot("a")
      slot("c")

    with pytest.raises(
      TypeError,
      match="unexpected keyword argument 'c'",
    ):
      _UserCompositeComponent(
        named_component_with_missing_slot, named_slots_cls=TestSlot
      )


# Test event types for disambiguation test
from dataclasses import dataclass


@dataclass(kw_only=True)
class TestBlurEvent(MesopEvent):
  """Test blur event."""

  value: str


@dataclass(kw_only=True)
class TestSelectEvent(MesopEvent):
  """Test select event."""

  values: list[str]


@pytest.mark.usefixtures("runtime")
def test_event_handler_disambiguation(runtime, app):
  """Test that the same handler can be registered with different event types."""
  with app.app_context():
    # Register event mappers
    runtime().register_event_mapper(
      TestBlurEvent,
      lambda userEvent, key: TestBlurEvent(
        value=userEvent.string_value,
        key=key.key,
      ),
    )
    runtime().register_event_mapper(
      TestSelectEvent,
      lambda userEvent, key: TestSelectEvent(
        values=["test"],
        key=key.key,
      ),
    )

    # Define a shared handler function
    def shared_handler(event):
      pass

    # Register the same handler with different event types
    blur_handler_id = register_event_handler(shared_handler, event=TestBlurEvent)
    select_handler_id = register_event_handler(
      shared_handler, event=TestSelectEvent
    )

    # The handler IDs should be different because they handle different event types
    assert (
      blur_handler_id != select_handler_id
    ), "Handler IDs should be different for different event types"

    # Get the registered handlers
    blur_handler = runtime().context()._handlers.get(blur_handler_id)
    select_handler = runtime().context()._handlers.get(select_handler_id)

    # Both handlers should exist
    assert blur_handler is not None, "Blur handler should be registered"
    assert select_handler is not None, "Select handler should be registered"

    # Create mock events
    blur_proto = pb.UserEvent(
      string_value="blur_value",
      key=pb.Key(key="test_key"),
    )
    select_proto = pb.UserEvent(
      string_value="",
      key=pb.Key(key="test_key"),
    )

    # Call the handlers and verify they use the correct event mappers
    blur_handler(blur_proto)
    select_handler(select_proto)


if __name__ == "__main__":
  raise SystemExit(pytest.main([__file__]))
