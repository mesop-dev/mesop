from dataclasses import dataclass, field
from datetime import date, datetime

import numpy as np
import pandas as pd
import pytest
from pydantic import BaseModel

import mesop.protos.ui_pb2 as pb
from mesop.components.uploader.uploaded_file import UploadedFile
from mesop.dataclass_utils.dataclass_utils import (
  dataclass_with_defaults,
  has_parent,
  serialize_dataclass,
  update_dataclass_from_json,
)
from mesop.exceptions import MesopDeveloperException


@dataclass
class C:
  val: str = "<init>"


@dataclass
class B:
  c: C = field(default_factory=C)


@dataclass
class A:
  b: B = field(default_factory=B)
  list_b: list[B] = field(default_factory=list)
  datetimes: list[datetime] = field(
    default_factory=lambda: [datetime(1974, 1, 1)]
  )
  dates: list[date] = field(default_factory=lambda: [date(1974, 1, 1)])
  strs: list[str] = field(default_factory=list)
  str_dict: dict[str, str] = field(default_factory=dict)


@dataclass
class WithPandasDataFrame:
  val: pd.DataFrame | None = None


@dataclass
class WithBytes:
  data: bytes = b""


@dataclass
class WithUploadedFile:
  data: UploadedFile = field(default_factory=UploadedFile)


class NestedPydanticModel(BaseModel):
  default_value: str = "default"
  no_default_value: str


class PydanticModel(BaseModel):
  name: str = "World"
  counter: int = 0
  list_models: list[NestedPydanticModel] = field(default_factory=lambda: [])
  nested: NestedPydanticModel = field(
    default_factory=lambda: NestedPydanticModel(
      no_default_value="<no_default_factory>"
    )
  )
  optional_value: str | None = None
  union_value: str | int = 0
  tuple_value: tuple[str, int] = ("a", 1)


@dataclass_with_defaults
class WithPydanticModel:
  data: PydanticModel


@dataclass_with_defaults
class WithPydanticModelDefaultFactory:
  default_factory: PydanticModel = field(default_factory=PydanticModel)


JSON_STR = """{"b": {"c": {"val": "<init>"}},
"list_b": [
  {"c": {"val": "1"}},
  {"c": {"val": "2"}}
],
"datetimes": [
  {"__datetime.datetime__": "1972-01-01T02:00:30"},
  {"__datetime.datetime__": "2024-06-12T05:01:30"}
],
"dates": [
  {"__datetime.date__": "1972-01-01"},
  {"__datetime.date__": "2024-06-12"}
],
"strs": ["a", "b"]}"""


@dataclass_with_defaults
class DataclassNoDefaults:
  foo: int
  dict: dict[str, str]


class UnannotatedClass:
  val: str


@dataclass_with_defaults
class NestedDataclassNoDefaults:
  a: DataclassNoDefaults
  list_a: list[DataclassNoDefaults]
  unannotated: UnannotatedClass


def test_dataclass_defaults():
  d = DataclassNoDefaults()
  assert d.foo == 0


def test_dataclass_defaults_recursive():
  d = NestedDataclassNoDefaults()
  assert d.a.foo == 0
  assert d.list_a == []
  assert d.unannotated.val == ""


def test_dataclass_field_defaults_works_with_already_annotated_nested_class():
  @dataclass
  class NestedDataclass:
    val: str = field(default="<default>")

  @dataclass_with_defaults
  class RootDataclass:
    nested: NestedDataclass

  instance = RootDataclass()
  assert instance.nested.val == "<default>"


def test_dataclass_defaults_works_with_already_annotated_nested_class():
  @dataclass
  class NestedDataclass:
    val: str = "default"

  @dataclass_with_defaults
  class RootDataclass:
    nested: NestedDataclass

  instance = RootDataclass()
  assert instance.nested.val == "default"


def test_dataclass_defaults_works_with_already_annotated_nested_class_fails_without_default():
  @dataclass
  class NestedDataclass:
    val: str

  @dataclass_with_defaults
  class RootDataclass:
    nested: NestedDataclass

  with pytest.raises(TypeError) as exc_info:
    RootDataclass()
  assert "missing 1 required positional argument: 'val'" in str(exc_info.value)


def test_serialize_dataclass():
  val = serialize_dataclass(A())
  assert (
    val
    == """{"b": {"c": {"val": "<init>"}}, "list_b": [], "datetimes": [{"__datetime.datetime__": "1974-01-01T00:00:00"}], "dates": [{"__datetime.date__": "1974-01-01"}], "strs": [], "str_dict": {}}"""
  )


def test_serialize_pandas_dataframe():
  df = pd.DataFrame(
    data={
      "NA": [pd.NA, pd.NA],
      "Bools": [True, np.bool_(False)],
      "Ints": [101, np.int64(-55)],
      "Floats": [2.3, np.float64(-3.000000003)],
      "Strings": ["Hello", "World"],
      "DateTimes": [
        pd.Timestamp("20180310"),
        pd.Timestamp("20230310"),
      ],
    }
  )

  serialized_dataclass = serialize_dataclass(WithPandasDataFrame(val=df))

  json_data = df.to_json(orient="table")
  assert json_data is not None
  assert (
    serialized_dataclass
    == '{"val": {"__pandas.DataFrame__": "'
    + json_data.replace('"', '\\"')
    + '"}}'
  )


def test_serialize_uploaded_file():
  serialized_dataclass = serialize_dataclass(
    WithUploadedFile(
      data=UploadedFile(
        b"data", name="file.png", size=10, mime_type="image/png"
      )
    )
  )

  assert (
    serialized_dataclass
    == '{"data": {"__mesop.UploadedFile__": {"contents": "ZGF0YQ==", "name": "file.png", "size": 10, "mime_type": "image/png"}}}'
  )


def test_serialize_deserialize_pydantic_model():
  state = WithPydanticModel()
  state.data.name = "Hello"
  state.data.counter = 1
  state.data.nested = NestedPydanticModel(no_default_value="no_default")
  state.data.list_models.append(
    NestedPydanticModel(no_default_value="no_default_list_model_val_1")
  )
  state.data.list_models.append(
    NestedPydanticModel(no_default_value="no_default_list_model_val_2")
  )
  new_state = WithPydanticModel()
  update_dataclass_from_json(new_state, serialize_dataclass(state))
  assert new_state == state


def test_serialize_deserialize_pydantic_model_set_optional_value():
  state = WithPydanticModel()
  state.data.optional_value = "optional"
  new_state = WithPydanticModel()
  update_dataclass_from_json(new_state, serialize_dataclass(state))
  assert new_state == state


def test_serialize_deserialize_pydantic_model_set_union_value():
  state = WithPydanticModel()
  state.data.union_value = "union_value"
  new_state = WithPydanticModel()
  update_dataclass_from_json(new_state, serialize_dataclass(state))
  assert new_state == state


def test_serialize_deserialize_pydantic_model_set_tuple_value():
  state = WithPydanticModel()
  state.data.tuple_value = ("tuple_value", 1)
  new_state = WithPydanticModel()
  update_dataclass_from_json(new_state, serialize_dataclass(state))
  assert new_state == state


def test_serialize_deserialize_pydantic_model_default_factory():
  state = WithPydanticModelDefaultFactory()
  state.default_factory.name = "Hello"
  state.default_factory.counter = 1
  state.default_factory.nested = NestedPydanticModel(
    no_default_value="no_default"
  )
  new_state = WithPydanticModelDefaultFactory()
  update_dataclass_from_json(new_state, serialize_dataclass(state))
  assert new_state == state


@pytest.mark.parametrize(
  "input_bytes, expected_json",
  [
    (b"hello world", '{"data": {"__python.bytes__": "aGVsbG8gd29ybGQ="}}'),
    (b"", '{"data": {"__python.bytes__": ""}}'),
  ],
)
def test_serialize_bytes(input_bytes, expected_json):
  serialized_dataclass = serialize_dataclass(WithBytes(data=input_bytes))
  assert serialized_dataclass == expected_json


@pytest.mark.parametrize(
  "input_set, expected_json",
  [
    ({1, 2, 3}, '{"data": {"__python.set__": [1, 2, 3]}}'),
    (set(), '{"data": {"__python.set__": []}}'),
  ],
)
def test_serialize_set(input_set, expected_json):
  serialized_dataclass = serialize_dataclass(WithBytes(data=input_set))
  assert serialized_dataclass == expected_json


def test_update_dataclass_from_json_nested_dataclass():
  b = B()
  update_dataclass_from_json(b, """{"c": {"val": "<init>"}}""")
  assert b.c.val == "<init>"

  a = A()
  update_dataclass_from_json(a, JSON_STR)
  assert a.datetimes == [
    datetime(1972, 1, 1, 2, 0, 30),
    datetime(2024, 6, 12, 5, 1, 30),
  ]
  assert a.dates == [
    date(1972, 1, 1),
    date(2024, 6, 12),
  ]
  assert a.b.c.val == "<init>"


def test_update_dataclass_from_json_list_nested_dataclass():
  a = A()
  update_dataclass_from_json(a, JSON_STR)
  assert a.list_b == [
    B(c=C(val="1")),
    B(c=C(val="2")),
  ]
  assert a.strs == ["a", "b"]


def test_update_dataclass_with_pandas_dataframe():
  serialized_dataclass = serialize_dataclass(
    WithPandasDataFrame(
      val=pd.DataFrame(
        data={
          "NA": [pd.NA, pd.NA],
          "Bools": [True, np.bool_(False)],
          "Ints": [101, np.int64(-55)],
          "Floats": [2.3, np.float64(-3.000000003)],
          "Strings": ["Hello", "World"],
          "DateTimes": [
            pd.Timestamp("20180310"),
            pd.Timestamp("20230310"),
          ],
        }
      )
    )
  )
  pandas_dataframe_state = WithPandasDataFrame()

  update_dataclass_from_json(pandas_dataframe_state, serialized_dataclass)

  assert pandas_dataframe_state.val is not None
  assert pandas_dataframe_state.val.equals(
    pd.DataFrame(
      data={
        "NA": [
          np.nan,
          np.nan,
        ],  # Note that these became np.nan instead of pd.NA.
        "Bools": [True, np.bool_(False)],
        "Ints": [101, np.int64(-55)],
        "Floats": [2.3, np.float64(-3.000000003)],
        "Strings": ["Hello", "World"],
        "DateTimes": [
          pd.Timestamp("20180310"),
          pd.Timestamp("20230310"),
        ],
      }
    )
  )


def test_update_dataclass_with_uploaded_file():
  uploaded_file = UploadedFile(
    b"data", name="file.png", size=10, mime_type="image/png"
  )
  serialized_dataclass = serialize_dataclass(
    WithUploadedFile(data=uploaded_file)
  )
  uploaded_file_state = WithUploadedFile()
  update_dataclass_from_json(uploaded_file_state, serialized_dataclass)
  assert uploaded_file_state.data == uploaded_file


def test_update_dataclass_with_bytes():
  bytes_data = b"hello world"
  serialized_dataclass = serialize_dataclass(WithBytes(data=bytes_data))
  bytes_state = WithBytes()
  update_dataclass_from_json(bytes_state, serialized_dataclass)
  assert bytes_state.data == bytes_data


def test_update_dataclass_with_set():
  @dataclass
  class StateWithSet:
    data: set = field(default_factory=set)

  serialized_dataclass = serialize_dataclass(StateWithSet(data={1, 2, 4}))
  set_state = StateWithSet()
  update_dataclass_from_json(set_state, serialized_dataclass)
  assert set_state.data == {1, 2, 4}


def test_update_dataclass_with_nested_set():
  @dataclass
  class StateWithSet:
    data: list[set] = field(default_factory=list)

  serialized_dataclass = serialize_dataclass(
    StateWithSet(data=[{1, 2, 4}, {5, 6}])
  )
  set_state = StateWithSet()
  update_dataclass_from_json(set_state, serialized_dataclass)
  assert set_state.data == [{1, 2, 4}, {5, 6}]


@dataclass_with_defaults
class StateWithDict:
  a_dict: dict[str, bool]


def test_serialize_deserialize_state_with_dict():
  state = StateWithDict()
  state.a_dict["a"] = True
  state.a_dict["b"] = False
  new_state = StateWithDict()
  update_dataclass_from_json(new_state, serialize_dataclass(state))
  assert new_state == state


@dataclass_with_defaults
class StateWithNestedDict:
  nested_dict: dict[str, dict[str, bool]]


def test_serialize_deserialize_state_with_nested_dict():
  state = StateWithNestedDict()
  state.nested_dict["a"] = {"inner": True, "inner2": False}
  state.nested_dict["b"] = {"val": True}
  new_state = StateWithNestedDict()
  update_dataclass_from_json(new_state, serialize_dataclass(state))
  assert new_state == state


@dataclass_with_defaults
class StateWithNestedList:
  nested_list: list[list[str]]


def test_serialize_deserialize_state_with_nested_list():
  state = StateWithNestedList()
  state.nested_list.append(["a", "b"])
  state.nested_list.append([])
  new_state = StateWithNestedList()
  update_dataclass_from_json(new_state, serialize_dataclass(state))
  assert new_state == state


@dataclass_with_defaults
class StateWithListDict:
  list_dict: list[dict[str, bool]]


def test_serialize_deserialize_state_with_list_dict():
  state = StateWithListDict()
  state.list_dict.append({"firstEl": True})
  state.list_dict.append({"2A": True, "2B": False})
  new_state = StateWithListDict()
  update_dataclass_from_json(new_state, serialize_dataclass(state))
  assert new_state == state


def test_serialize_deserialize_state_with_proto_throws():
  @dataclass_with_defaults
  class State:
    proto: pb.ComponentName

  state = State()

  with pytest.raises(Exception) as exc_info:
    serialize_dataclass(state)

  assert "Object of type ComponentName is not JSON serializable" in str(
    exc_info.value
  )


def test_dataclass_default_value_throws():
  with pytest.raises(Exception) as exc_info:

    @dataclass
    class MutableDataclass:
      str_value: str

    @dataclass_with_defaults
    class StateWithMutableDefaultDataclassValue:
      value: MutableDataclass = MutableDataclass(str_value="abc")

  assert (
    "mutable default <class 'dataclass_utils.dataclass_utils_test.test_dataclass_default_value_throws.<locals>.MutableDataclass'> for field value is not allowed"
    in str(exc_info.value)
  )


def test_proto_without_default_does_not_throw():
  @dataclass_with_defaults
  class StateWithMutableProto:
    proto: pb.Style


def test_proto_with_default_throws():
  with pytest.raises(Exception) as exc_info:

    @dataclass_with_defaults
    class StateWithMutableProto:
      proto: pb.Style = pb.Style()

  assert (
    "mutable default <class 'mesop.protos.ui_pb2.Style'> for field proto is not allowed"
    in str(exc_info.value)
  )


def test_proto_in_dataclass_without_default_does_not_throw():
  @dataclass
  class DataclassWithProto:
    style: pb.Style

  @dataclass_with_defaults
  class StateWithMutableProto:
    dataclass: DataclassWithProto


def test_proto_in_dataclass_with_default_throws():
  with pytest.raises(Exception) as exc_info:

    @dataclass
    class DataclassWithProto:
      style: pb.Style = pb.Style()  # noqa: RUF009 (intentionally do an anti-pattern to make sure exception is raised)

    @dataclass_with_defaults
    class StateWithMutableProto:
      dataclass: DataclassWithProto

  assert (
    "mutable default <class 'mesop.protos.ui_pb2.Style'> for field style is not allowed"
    in str(exc_info.value)
  )


def test_proto_in_unannotated_class_without_default_does_not_throw():
  class UnannotatedClassWithProto:
    style: pb.Style

  @dataclass_with_defaults
  class StateWithMutableProto:
    dataclass: UnannotatedClassWithProto


def test_proto_in_unannotated_class_with_default_throws():
  with pytest.raises(Exception) as exc_info:

    class UnannotatedClassWithProto:
      style: pb.Style = pb.Style()

    @dataclass_with_defaults
    class StateWithMutableProto:
      dataclass: UnannotatedClassWithProto

  assert (
    "mutable default <class 'mesop.protos.ui_pb2.Style'> for field style is not allowed"
    in str(exc_info.value)
  )


def test_has_parent_simple_class():
  class SimpleClass:
    val: str

  assert has_parent(SimpleClass) is False


def test_has_parent_dataclass():
  @dataclass
  class ADataclass:
    val: str

  assert has_parent(ADataclass) is False


def test_has_parent_child_class():
  class ParentClass:
    pass

  class ChildClass(ParentClass):
    val: str

  assert has_parent(ChildClass) is True
  assert has_parent(ParentClass) is False


def test_globals_pollution():
  @dataclass
  class A:
    val: str

  initial_name = __name__
  obj = A(val="default")
  with pytest.raises(MesopDeveloperException) as exc_info:
    update_dataclass_from_json(
      obj, '{"__init__": {"__globals__": {"__name__": "polluted"}}}'
    )
  assert "Cannot use dunder property: __init__ in stateclass" in str(
    exc_info.value
  )
  # Make sure __name__ has not been modified via the __globals__ pollution attempt
  assert __name__ == initial_name


def test_class_level_attribute_pollution_blocked():
  """Regression test for class-level mutable attribute pollution.

  A non-dunder key that resolves to a class-level attribute (rather than a
  declared dataclass field) must be rejected, since setting it would mutate
  state shared across all sessions instead of the per-instance field.
  """

  class MutableRoleMap(dict):
    __hash__ = object.__hash__  # (mimic a hashable-but-mutable gadget)

  class RoleService:
    # Class-level (not annotated, so not a dataclass field) shared mapping.
    role_map = MutableRoleMap({"assistant": "user"})

  @dataclass
  class ChatState:
    service: RoleService = field(default_factory=RoleService)

  state = ChatState()
  with pytest.raises(MesopDeveloperException) as exc_info:
    update_dataclass_from_json(
      state, '{"service": {"role_map": {"assistant": "system"}}}'
    )
  assert (
    "Cannot set non-dataclass-field property: role_map in stateclass"
    in str(exc_info.value)
  )
  # Make sure the shared class-level mapping was not mutated.
  assert RoleService.role_map == {"assistant": "user"}


if __name__ == "__main__":
  raise SystemExit(pytest.main(["-vv", __file__]))
