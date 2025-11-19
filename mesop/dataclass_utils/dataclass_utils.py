# ruff: noqa: E721
import base64
import json
from dataclasses import Field, asdict, dataclass, field, is_dataclass
from datetime import date, datetime
from io import StringIO
from typing import Any, Type, TypeVar, cast, get_origin, get_type_hints

from deepdiff import DeepDiff, Delta
from deepdiff.operator import BaseOperator
from deepdiff.path import parse_path
from pydantic import BaseModel

from mesop.components.uploader.uploaded_file import UploadedFile
from mesop.exceptions import MesopDeveloperException, MesopException

_PANDAS_OBJECT_KEY = "__pandas.DataFrame__"
_DATE_OBJECT_KEY = "__datetime.date__"
_PYDANTIC_OBJECT_KEY = "__pydantic.BaseModel__"
_DATETIME_OBJECT_KEY = "__datetime.datetime__"
_BYTES_OBJECT_KEY = "__python.bytes__"
_SET_OBJECT_KEY = "__python.set__"
_UPLOADED_FILE_OBJECT_KEY = "__mesop.UploadedFile__"
_DIFF_ACTION_DATA_FRAME_CHANGED = "data_frame_changed"
_DIFF_ACTION_EQUALITY_CHANGED = "mesop_equality_changed"

C = TypeVar("C")


def _check_has_pandas():
  """Checks if pandas exists since it is an optional dependency for Mesop."""
  try:
    import pandas  # noqa: F401

    return True
  except ImportError:
    return False


_has_pandas = _check_has_pandas()

pydantic_model_cache = {}


def dataclass_with_defaults(cls: Type[C]) -> Type[C]:
  """
  Provides defaults for every attribute in a dataclass (recursively) so
  Mesop developers don't need to manually set default values
  """

  # Make sure that none of the class variables use a mutable default value
  # which can cause state to be accidentally shared across sessions which can
  # be very bad!
  for name in cls.__dict__:
    # Skip dunder methods/attributes.
    if name.startswith("__") and name.endswith("__"):
      continue
    classVar = cls.__dict__[name]
    if not isinstance(classVar, Field):
      try:
        # If a value is not hashable, then we will treat it as mutable.
        hash(classVar)
      except TypeError as exc:
        error_message = (
          f"mutable default {type(classVar)} for field {name} is not allowed: use default_factory for state class {cls.__name__}. "
          "See: https://mesop-dev.github.io/mesop/guides/state-management/#use-immutable-default-values"
        )
        raise MesopDeveloperException(error_message) from exc

  annotations = get_type_hints(cls)
  for name, type_hint in annotations.items():
    if (
      isinstance(type_hint, type)
      and has_parent(type_hint)
      and issubclass(type_hint, BaseModel)
    ):
      pydantic_model_cache[(type_hint.__module__, type_hint.__qualname__)] = (
        type_hint
      )
    if name not in cls.__dict__:  # Skip if default already set
      if type_hint == int:
        setattr(cls, name, field(default=0))
      elif type_hint == float:
        setattr(cls, name, field(default=0.0))
      elif type_hint == str:
        setattr(cls, name, field(default=""))
      elif type_hint == bool:
        setattr(cls, name, field(default=False))
      elif get_origin(type_hint) == list:
        setattr(cls, name, field(default_factory=list))
      elif get_origin(type_hint) == dict:
        setattr(cls, name, field(default_factory=dict))
      elif isinstance(type_hint, type):
        if has_parent(type_hint):
          # If this isn't a simple class (i.e. it inherits from another class)
          # then we will preserve its semantics (not try to set default values
          # because it's not a dataclass) and instantiate it with each new instance
          # of a state class.
          setattr(cls, name, field(default_factory=type_hint))
        else:
          # If it's a simple dataclass (i.e. does not inherit from another class)
          # then we will try to set default values and then wrap it with a dataclass
          # decorator (if necessary).
          setattr(
            cls, name, field(default_factory=dataclass_with_defaults(type_hint))
          )
  # If a class is already a dataclass, then don't wrap it with another dataclass decorator.
  if is_dataclass(cls):
    return cls
  return dataclass(cls)


def has_parent(cls: Type[Any]) -> bool:
  return len(cls.__bases__) > 0 and cls.__bases__[0] != object


def serialize_dataclass(state: Any):
  if is_dataclass(state):
    json_str = json.dumps(asdict(state), cls=MesopJSONEncoder)
    return json_str
  else:
    raise MesopException("Tried to serialize state which was not a dataclass")


def update_dataclass_from_json(instance: Any, json_string: str):
  data = json.loads(json_string, object_hook=decode_mesop_json_state_hook)
  _recursive_update_dataclass_from_json_obj(instance, data)


def _recursive_update_dataclass_from_json_obj(instance: Any, json_dict: Any):
  for key, value in json_dict.items():
    if key.startswith("__") and key.endswith("__"):
      raise MesopDeveloperException(
        f"Cannot use dunder property: {key} in stateclass"
      )
    if hasattr(instance, key):
      attr = getattr(instance, key)
      if isinstance(value, dict):
        # If the value is a dict, recursively update the dataclass.
        setattr(
          instance,
          key,
          _recursive_update_dataclass_from_json_obj(attr, value),
        )
      elif isinstance(value, list):
        updated_list: list[Any] = []
        for item in cast(list[Any], value):
          if isinstance(item, dict):
            # If the json item value is an instance of dict
            # and the instance has an attribute with a matching name,
            # we assume the dict should be converted into a dataclass.
            attr = getattr(instance, key)
            item_instance = instance.__annotations__[key].__args__[0]()
            updated_list.append(
              _recursive_update_dataclass_from_json_obj(item_instance, item)
            )
          else:
            # If the item is not a dict, append it directly.
            updated_list.append(item)
        setattr(instance, key, updated_list)
      else:
        # For other types, set the value directly.
        setattr(instance, key, value)
    else:
      if isinstance(instance, dict):
        instance[key] = value
      else:
        raise MesopException(
          f"Unhandled stateclass deserialization where key={key}, value={value}, instance={instance}"
        )
  return instance


class MesopJSONEncoder(json.JSONEncoder):
  """
  Custom JSON Encoder to handle special serialization cases.

  Since we support Pandas DataFrames in the Mesop table, users may need to store the
  the DataFrames in Mesop State. This means we need a way to serialize the DataFrame to
  JSON and back.

  For simplicity we will convert the DataFrame to JSON within the JSON serialized state.
  This makes it so we don't have to worry about serializing other data types used by
  Pandas. The "table" serialization format is verbose, but will ensure the most accurate
  deserialization back into a DataFrame.
  """

  def default(self, obj):
    try:
      import pandas as pd

      if isinstance(obj, pd.DataFrame):
        return {_PANDAS_OBJECT_KEY: pd.DataFrame.to_json(obj, orient="table")}
    except ImportError:
      pass

    if isinstance(obj, UploadedFile):
      return {
        _UPLOADED_FILE_OBJECT_KEY: {
          "contents": base64.b64encode(obj.getvalue()).decode("utf-8"),
          "name": obj.name,
          "size": obj.size,
          "mime_type": obj.mime_type,
        }
      }

    if isinstance(obj, BaseModel):
      return {
        _PYDANTIC_OBJECT_KEY: {
          "json": obj.model_dump_json(),
          "module": obj.__class__.__module__,
          "qualname": obj.__class__.__qualname__,
        }
      }

    if isinstance(obj, datetime):
      return {_DATETIME_OBJECT_KEY: obj.isoformat()}

    if isinstance(obj, date):
      return {_DATE_OBJECT_KEY: obj.isoformat()}

    if isinstance(obj, bytes):
      return {_BYTES_OBJECT_KEY: base64.b64encode(obj).decode("utf-8")}

    if isinstance(obj, set):
      return {_SET_OBJECT_KEY: list(obj)}

    if isinstance(obj, type):
      return str(obj)

    if is_dataclass(obj):
      return asdict(obj)

    return super().default(obj)


def decode_mesop_json_state_hook(dct):
  """
  Object hook to decode JSON for Mesop state.

  Since we support Pandas DataFrames in the Mesop table, users may need to store the
  the DataFrames in Mesop State. This means we need a way to serialize the DataFrame to
  JSON and back.

  One thing to note is that pandas.NA becomes numpy.nan during deserialization.
  """
  if _has_pandas:
    import pandas as pd

    if _PANDAS_OBJECT_KEY in dct:
      return pd.read_json(StringIO(dct[_PANDAS_OBJECT_KEY]), orient="table")

  if _PYDANTIC_OBJECT_KEY in dct:
    cache_key = (
      dct[_PYDANTIC_OBJECT_KEY]["module"],
      dct[_PYDANTIC_OBJECT_KEY]["qualname"],
    )
    if cache_key not in pydantic_model_cache:
      raise MesopException(
        f"Tried to deserialize Pydantic model, but it's not in the cache: {cache_key}"
      )
    model_class = pydantic_model_cache[cache_key]
    return model_class.model_validate_json(dct[_PYDANTIC_OBJECT_KEY]["json"])

  if _DATETIME_OBJECT_KEY in dct:
    return datetime.fromisoformat(dct[_DATETIME_OBJECT_KEY])

  if _DATE_OBJECT_KEY in dct:
    return date.fromisoformat(dct[_DATE_OBJECT_KEY])

  if _BYTES_OBJECT_KEY in dct:
    return base64.b64decode(dct[_BYTES_OBJECT_KEY])

  if _SET_OBJECT_KEY in dct:
    return set(dct[_SET_OBJECT_KEY])

  if _UPLOADED_FILE_OBJECT_KEY in dct:
    return UploadedFile(
      base64.b64decode(dct[_UPLOADED_FILE_OBJECT_KEY]["contents"]),
      name=dct[_UPLOADED_FILE_OBJECT_KEY]["name"],
      size=dct[_UPLOADED_FILE_OBJECT_KEY]["size"],
      mime_type=dct[_UPLOADED_FILE_OBJECT_KEY]["mime_type"],
    )

  return dct


class DataFrameOperator(BaseOperator):
  """Custom operator to detect changes in DataFrames.

  DeepDiff does not support diffing DataFrames. See https://github.com/seperman/deepdiff/issues/394.

  This operator checks if the DataFrames are equal or not. It does not do a deep diff of
  the contents of the DataFrame.
  """

  def match(self, level) -> bool:
    try:
      import pandas as pd

      return isinstance(level.t1, pd.DataFrame) and isinstance(
        level.t2, pd.DataFrame
      )
    except ImportError:
      # If Pandas is not installed, don't perform this check. We should log a warning.
      return False

  def normalize_value_for_hashing(self, parent: Any, obj: Any) -> Any:
    return obj

  def give_up_diffing(self, level, diff_instance) -> bool:
    if not level.t1.equals(level.t2):
      diff_instance.custom_report_result(
        _DIFF_ACTION_DATA_FRAME_CHANGED, level, {"value": level.t2}
      )
    return True


class EqualityOperator(BaseOperator):
  """Custom operator to detect changes with direct equality.

  DeepDiff does not diff the UploadedFile class correctly, so we will just use a normal
  equality check, rather than diffing further into the io.BytesIO parent class.
  """

  def match(self, level) -> bool:
    return isinstance(level.t1, (UploadedFile, BaseModel)) and isinstance(
      level.t2, (UploadedFile, BaseModel)
    )

  def normalize_value_for_hashing(self, parent: Any, obj: Any) -> Any:
    if isinstance(obj, set):
      return set(sorted(list(obj)))
    return obj

  def give_up_diffing(self, level, diff_instance) -> bool:
    if level.t1 != level.t2:
      diff_instance.custom_report_result(
        _DIFF_ACTION_EQUALITY_CHANGED, level, {"value": level.t2}
      )
    return True


def diff_state(state1: Any, state2: Any) -> str:
  """
  Diffs two state objects and returns the difference using DeepDiff's Delta format as a
  JSON string.

  DeepDiff does not support DataFrames yet. See `DataFrameOperator`.

  The `to_flat_dicts` method does not include custom report results, so we need to add
  those manually for the DataFrame case.
  """
  if not is_dataclass(state1) or not is_dataclass(state2):
    raise MesopException("Tried to diff state which was not a dataclass")

  custom_actions = []
  custom_operators = [EqualityOperator()]
  # Only use the `DataFrameOperator` if pandas exists.
  if _has_pandas:
    differences = DeepDiff(
      state1,
      state2,
      custom_operators=[*custom_operators, DataFrameOperator()],
      threshold_to_diff_deeper=0,
    )

    # Manually format dataframe diffs to flat dict format.
    if _DIFF_ACTION_DATA_FRAME_CHANGED in differences:
      custom_actions = [
        {
          "path": parse_path(path),
          "action": _DIFF_ACTION_DATA_FRAME_CHANGED,
          **diff,
        }
        for path, diff in differences[_DIFF_ACTION_DATA_FRAME_CHANGED].items()
      ]
  else:
    differences = DeepDiff(
      state1,
      state2,
      custom_operators=custom_operators,
      threshold_to_diff_deeper=0,
    )

  # Manually format diffs to flat dict format.
  if _DIFF_ACTION_EQUALITY_CHANGED in differences:
    custom_actions = [
      {
        "path": parse_path(path),
        "action": _DIFF_ACTION_EQUALITY_CHANGED,
        **diff,
      }
      for path, diff in differences[_DIFF_ACTION_EQUALITY_CHANGED].items()
    ]

  # Handle the set case which will have a modified path after being JSON encoded.
  diffs = []
  for action in Delta(differences, always_include_values=True).to_flat_dicts():
    if action["action"].startswith("set_item_"):  # type: ignore
      action["path"] = action["path"] + ["__python.set__"]  # type: ignore
    diffs.append(action)

  return json.dumps(diffs + custom_actions, cls=MesopJSONEncoder)
