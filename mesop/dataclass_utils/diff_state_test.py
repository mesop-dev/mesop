import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest
from pydantic import BaseModel

from mesop.components.uploader.uploaded_file import UploadedFile
from mesop.dataclass_utils.dataclass_utils import diff_state
from mesop.exceptions import MesopException


def test_no_diff():
  @dataclass
  class C:
    val1: str = "val1"

  assert json.loads(diff_state(C(), C())) == []


def test_diff_primitives():
  @dataclass
  class C:
    val1: str = "val1"
    val2: int = 1
    val3: float = 1.1
    val4: bool = True
    val5: bool | None = True

  s1 = C()
  s2 = C(val1="VAL1", val2=2, val3=1.2, val4=False, val5=None)
  assert json.loads(diff_state(s1, s2)) == [
    {
      "path": ["val5"],
      "action": "type_changes",
      "value": None,
      "type": "<class 'NoneType'>",
      "old_type": "<class 'bool'>",
      "old_value": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
    {
      "path": ["val1"],
      "action": "values_changed",
      "value": "VAL1",
      "type": "<class 'str'>",
      "old_type": "unknown___",
      "old_value": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
    {
      "path": ["val2"],
      "action": "values_changed",
      "value": 2,
      "type": "<class 'int'>",
      "old_type": "unknown___",
      "old_value": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
    {
      "path": ["val3"],
      "action": "values_changed",
      "value": 1.2,
      "type": "<class 'float'>",
      "old_type": "unknown___",
      "old_value": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
    {
      "path": ["val4"],
      "action": "values_changed",
      "value": False,
      "type": "<class 'bool'>",
      "old_type": "unknown___",
      "old_value": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
  ]


def test_diff_core_data_structures():
  @dataclass
  class C:
    val1: list[int] = field(default_factory=lambda: [1, 2, 3])
    val2: dict[str, str] = field(default_factory=lambda: {"k1": "v1"})
    val3: tuple[str, str] = field(default_factory=lambda: ("t1", "t2"))

  s1 = C()
  s2 = C(val1=[2, 3, 4], val2={"k2": "v2"}, val3=("t2", "t1"))

  assert json.loads(diff_state(s1, s2)) == [
    {
      "path": ["val2", "k2"],
      "action": "dictionary_item_added",
      "value": "v2",
      "old_value": "unknown___",
      "type": "<class 'str'>",
      "old_type": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
    {
      "path": ["val2", "k1"],
      "action": "dictionary_item_removed",
      "value": "v1",
      "old_value": "unknown___",
      "type": "<class 'str'>",
      "old_type": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
    {
      "path": ["val3", 0],
      "action": "values_changed",
      "value": "t2",
      "old_value": "unknown___",
      "type": "<class 'str'>",
      "old_type": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
    {
      "path": ["val3", 1],
      "action": "values_changed",
      "value": "t1",
      "old_value": "unknown___",
      "type": "<class 'str'>",
      "old_type": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
    {
      "path": ["val1"],
      "action": "iterable_items_deleted",
      "value": [],
      "old_value": [1],
      "type": "<class 'list'>",
      "old_type": "<class 'list'>",
      "new_path": None,
      "t1_from_index": 0,
      "t1_to_index": 1,
      "t2_from_index": 0,
      "t2_to_index": 0,
    },
    {
      "path": ["val1"],
      "action": "iterable_items_equal",
      "value": None,
      "old_value": None,
      "type": "<class 'NoneType'>",
      "old_type": "<class 'NoneType'>",
      "new_path": None,
      "t1_from_index": 1,
      "t1_to_index": 3,
      "t2_from_index": 0,
      "t2_to_index": 2,
    },
    {
      "path": ["val1"],
      "action": "iterable_items_inserted",
      "value": [4],
      "old_value": [],
      "type": "<class 'list'>",
      "old_type": "<class 'list'>",
      "new_path": None,
      "t1_from_index": 3,
      "t1_to_index": 3,
      "t2_from_index": 2,
      "t2_to_index": 3,
    },
  ]


def test_diff_nested_dataclass():
  @dataclass
  class B:
    val1: int = 1

  @dataclass
  class C:
    val1: B

  s1 = C(val1=B())
  s2 = C(val1=B(val1=2))

  assert json.loads(diff_state(s1, s2)) == [
    {
      "path": ["val1", "val1"],
      "action": "values_changed",
      "value": 2,
      "old_value": "unknown___",
      "type": "<class 'int'>",
      "old_type": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    }
  ]


def test_diff_nested_class():
  class B:
    def __init__(self, val1: int = 1):
      self.val1 = val1

  @dataclass
  class C:
    val1: B

  s1 = C(val1=B())
  s2 = C(val1=B(val1=2))
  print(json.loads(diff_state(s1, s2)))
  assert json.loads(diff_state(s1, s2)) == [
    {
      "path": ["val1", "val1"],
      "action": "values_changed",
      "value": 2,
      "old_value": "unknown___",
      "type": "<class 'int'>",
      "old_type": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    }
  ]


def test_diff_type_change():
  @dataclass
  class C:
    val1: str | bool = "String"

  s1 = C()
  s2 = C(val1=True)
  print(json.loads(diff_state(s1, s2)))
  assert json.loads(diff_state(s1, s2)) == [
    {
      "path": ["val1"],
      "action": "type_changes",
      "value": True,
      "old_value": "unknown___",
      "type": "<class 'bool'>",
      "old_type": "<class 'str'>",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    }
  ]


def test_diff_multiple_dict_changes():
  @dataclass
  class C:
    val1: dict[str, str] = field(
      default_factory=lambda: {
        "k1": "v1",
        "k2": "v2",
        "k3": "v3",
      }
    )

  s1 = C()
  s2 = C(
    val1={
      "k1": "V1",
      "k2": "v2",
      "k4": "v4",
      "k5": "v5",
    }
  )

  assert json.loads(diff_state(s1, s2)) == [
    {
      "path": ["val1", "k4"],
      "action": "dictionary_item_added",
      "value": "v4",
      "old_value": "unknown___",
      "type": "<class 'str'>",
      "old_type": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
    {
      "path": ["val1", "k5"],
      "action": "dictionary_item_added",
      "value": "v5",
      "old_value": "unknown___",
      "type": "<class 'str'>",
      "old_type": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
    {
      "path": ["val1", "k3"],
      "action": "dictionary_item_removed",
      "value": "v3",
      "old_value": "unknown___",
      "type": "<class 'str'>",
      "old_type": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
    {
      "path": ["val1", "k1"],
      "action": "values_changed",
      "value": "V1",
      "old_value": "unknown___",
      "type": "<class 'str'>",
      "old_type": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
  ]


def test_diff_nested_changes():
  @dataclass
  class B:
    val1: list[str | int]

  @dataclass
  class C:
    val1: dict[str, list[B]]

  s1 = C(
    val1={
      "k1": [B(val1=[1, 2, 3]), B(val1=[1])],
      "k2": [],
      "k3": [B(val1=[])],
    }
  )
  s2 = C(
    val1={
      "k1": [B(val1=[1, 2]), B(val1=[3, 4, 6, "2"])],
      "k2": [B(val1=[2, 2])],
      "k4": [B(val1=[])],
    }
  )

  assert json.loads(diff_state(s1, s2)) == [
    {
      "path": ["val1", "k4", 0],
      "value": {"val1": []},
      "action": "iterable_item_added",
      "old_value": "unknown___",
      "type": "<class 'dataclass_utils.diff_state_test.test_diff_nested_changes.<locals>.B'>",
      "old_type": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
    {
      "path": ["val1", "k3"],
      "action": "dictionary_item_removed",
      "value": [{"val1": []}],
      "old_value": "unknown___",
      "type": "<class 'list'>",
      "old_type": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
    {
      "path": ["val1", "k1", 1, "val1", 0],
      "action": "values_changed",
      "value": 3,
      "old_value": "unknown___",
      "type": "<class 'int'>",
      "old_type": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
    {
      "path": ["val1", "k1", 1, "val1", 1],
      "action": "iterable_item_added",
      "value": 4,
      "old_value": "unknown___",
      "type": "<class 'int'>",
      "old_type": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
    {
      "path": ["val1", "k1", 1, "val1", 2],
      "action": "iterable_item_added",
      "value": 6,
      "old_value": "unknown___",
      "type": "<class 'int'>",
      "old_type": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
    {
      "path": ["val1", "k1", 1, "val1", 3],
      "action": "iterable_item_added",
      "value": "2",
      "old_value": "unknown___",
      "type": "<class 'str'>",
      "old_type": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
    {
      "path": ["val1", "k2", 0],
      "action": "iterable_item_added",
      "value": {"val1": [2, 2]},
      "old_value": "unknown___",
      "type": "<class 'dataclass_utils.diff_state_test.test_diff_nested_changes.<locals>.B'>",
      "old_type": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
    {
      "path": ["val1", "k1", 0, "val1", 2],
      "action": "iterable_item_removed",
      "value": 3,
      "old_value": "unknown___",
      "type": "<class 'int'>",
      "old_type": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
  ]


def test_diff_weird_str_dict_keys():
  @dataclass
  class C:
    val1: dict[str, str] = field(
      default_factory=lambda: {
        "k-1": "v1",
        "k.2": "v2",
        "k 3": "v3",
      }
    )

  s1 = C()
  s2 = C(
    val1={
      "k-1": "V1",
      "k.2": "v2",
      "k 3": "v4",
    }
  )

  assert json.loads(diff_state(s1, s2)) == [
    {
      "path": ["val1", "k-1"],
      "action": "values_changed",
      "value": "V1",
      "old_value": "unknown___",
      "type": "<class 'str'>",
      "old_type": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
    {
      "path": ["val1", "k 3"],
      "action": "values_changed",
      "value": "v4",
      "old_value": "unknown___",
      "type": "<class 'str'>",
      "old_type": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
  ]


def test_diff_int_dict_keys():
  @dataclass
  class C:
    val1: dict[int, str] = field(
      default_factory=lambda: {
        1: "v1",
      }
    )

  s1 = C()
  s2 = C(
    val1={
      1: "V1",
    }
  )

  assert json.loads(diff_state(s1, s2)) == [
    {
      "path": ["val1", 1],
      "action": "values_changed",
      "value": "V1",
      "old_value": "unknown___",
      "type": "<class 'str'>",
      "old_type": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    }
  ]


# This looks like a bug.
def test_diff_tuple_dict_keys():
  @dataclass
  class C:
    val1: dict[tuple[int, int], str] = field(
      default_factory=lambda: {
        (1, 2): "v1",
      }
    )

  s1 = C()
  s2 = C(
    val1={
      (1, 2): "V1",
    }
  )

  assert json.loads(diff_state(s1, s2)) == [
    {
      "path": ["val1", 1, 2],
      "action": "values_changed",
      "value": "V1",
      "old_value": "unknown___",
      "type": "<class 'str'>",
      "old_type": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    }
  ]


def test_diff_multiple_iterable_changes():
  @dataclass
  class C:
    val1: list[int] = field(default_factory=lambda: [1, 2, 3, 4, 5, 6, 7])

  s1 = C()
  s2 = C(val1=[2, 3, 3, 4, 6])

  assert json.loads(diff_state(s1, s2)) == [
    {
      "path": ["val1"],
      "action": "iterable_items_deleted",
      "value": [],
      "old_value": [1],
      "type": "<class 'list'>",
      "old_type": "<class 'list'>",
      "new_path": None,
      "t1_from_index": 0,
      "t1_to_index": 1,
      "t2_from_index": 0,
      "t2_to_index": 0,
    },
    {
      "path": ["val1"],
      "action": "iterable_items_equal",
      "value": None,
      "old_value": None,
      "type": "<class 'NoneType'>",
      "old_type": "<class 'NoneType'>",
      "new_path": None,
      "t1_from_index": 1,
      "t1_to_index": 3,
      "t2_from_index": 0,
      "t2_to_index": 2,
    },
    {
      "path": ["val1"],
      "action": "iterable_items_inserted",
      "value": [3],
      "old_value": [],
      "type": "<class 'list'>",
      "old_type": "<class 'list'>",
      "new_path": None,
      "t1_from_index": 3,
      "t1_to_index": 3,
      "t2_from_index": 2,
      "t2_to_index": 3,
    },
    {
      "path": ["val1"],
      "action": "iterable_items_equal",
      "value": None,
      "old_value": None,
      "type": "<class 'NoneType'>",
      "old_type": "<class 'NoneType'>",
      "new_path": None,
      "t1_from_index": 3,
      "t1_to_index": 4,
      "t2_from_index": 3,
      "t2_to_index": 4,
    },
    {
      "path": ["val1"],
      "action": "iterable_items_deleted",
      "value": [],
      "old_value": [5],
      "type": "<class 'list'>",
      "old_type": "<class 'list'>",
      "new_path": None,
      "t1_from_index": 4,
      "t1_to_index": 5,
      "t2_from_index": 4,
      "t2_to_index": 4,
    },
    {
      "path": ["val1"],
      "action": "iterable_items_equal",
      "value": None,
      "old_value": None,
      "type": "<class 'NoneType'>",
      "old_type": "<class 'NoneType'>",
      "new_path": None,
      "t1_from_index": 5,
      "t1_to_index": 6,
      "t2_from_index": 4,
      "t2_to_index": 5,
    },
    {
      "path": ["val1"],
      "action": "iterable_items_deleted",
      "value": [],
      "old_value": [7],
      "type": "<class 'list'>",
      "old_type": "<class 'list'>",
      "new_path": None,
      "t1_from_index": 6,
      "t1_to_index": 7,
      "t2_from_index": 5,
      "t2_to_index": 5,
    },
  ]


def test_diff_multiple_iterable_deletions():
  @dataclass
  class C:
    val1: list[int] = field(default_factory=lambda: [1, 2, 3, 4, 5, 6, 7])
    val2: dict[str, list[int]] = field(
      default_factory=lambda: {
        "val2A": [10, 20, 30, 40, 50, 60, 70],
      }
    )

  s1 = C()
  s2 = C(
    val1=[2, 4, 6, 7],
    val2={
      "val2A": [10, 20, 40, 60, 70],
    },
  )

  assert json.loads(diff_state(s1, s2)) == [
    {
      "path": ["val1"],
      "action": "iterable_items_deleted",
      "value": [],
      "old_value": [1],
      "type": "<class 'list'>",
      "old_type": "<class 'list'>",
      "new_path": None,
      "t1_from_index": 0,
      "t1_to_index": 1,
      "t2_from_index": 0,
      "t2_to_index": 0,
    },
    {
      "path": ["val1"],
      "action": "iterable_items_equal",
      "value": None,
      "old_value": None,
      "type": "<class 'NoneType'>",
      "old_type": "<class 'NoneType'>",
      "new_path": None,
      "t1_from_index": 1,
      "t1_to_index": 2,
      "t2_from_index": 0,
      "t2_to_index": 1,
    },
    {
      "path": ["val1"],
      "action": "iterable_items_deleted",
      "value": [],
      "old_value": [3],
      "type": "<class 'list'>",
      "old_type": "<class 'list'>",
      "new_path": None,
      "t1_from_index": 2,
      "t1_to_index": 3,
      "t2_from_index": 1,
      "t2_to_index": 1,
    },
    {
      "path": ["val1"],
      "action": "iterable_items_equal",
      "value": None,
      "old_value": None,
      "type": "<class 'NoneType'>",
      "old_type": "<class 'NoneType'>",
      "new_path": None,
      "t1_from_index": 3,
      "t1_to_index": 4,
      "t2_from_index": 1,
      "t2_to_index": 2,
    },
    {
      "path": ["val1"],
      "action": "iterable_items_deleted",
      "value": [],
      "old_value": [5],
      "type": "<class 'list'>",
      "old_type": "<class 'list'>",
      "new_path": None,
      "t1_from_index": 4,
      "t1_to_index": 5,
      "t2_from_index": 2,
      "t2_to_index": 2,
    },
    {
      "path": ["val1"],
      "action": "iterable_items_equal",
      "value": None,
      "old_value": None,
      "type": "<class 'NoneType'>",
      "old_type": "<class 'NoneType'>",
      "new_path": None,
      "t1_from_index": 5,
      "t1_to_index": 7,
      "t2_from_index": 2,
      "t2_to_index": 4,
    },
    {
      "path": ["val2", "val2A"],
      "action": "iterable_items_equal",
      "value": None,
      "old_value": None,
      "type": "<class 'NoneType'>",
      "old_type": "<class 'NoneType'>",
      "new_path": None,
      "t1_from_index": 0,
      "t1_to_index": 2,
      "t2_from_index": 0,
      "t2_to_index": 2,
    },
    {
      "path": ["val2", "val2A"],
      "action": "iterable_items_deleted",
      "value": [],
      "old_value": [30],
      "type": "<class 'list'>",
      "old_type": "<class 'list'>",
      "new_path": None,
      "t1_from_index": 2,
      "t1_to_index": 3,
      "t2_from_index": 2,
      "t2_to_index": 2,
    },
    {
      "path": ["val2", "val2A"],
      "action": "iterable_items_equal",
      "value": None,
      "old_value": None,
      "type": "<class 'NoneType'>",
      "old_type": "<class 'NoneType'>",
      "new_path": None,
      "t1_from_index": 3,
      "t1_to_index": 4,
      "t2_from_index": 2,
      "t2_to_index": 3,
    },
    {
      "path": ["val2", "val2A"],
      "action": "iterable_items_deleted",
      "value": [],
      "old_value": [50],
      "type": "<class 'list'>",
      "old_type": "<class 'list'>",
      "new_path": None,
      "t1_from_index": 4,
      "t1_to_index": 5,
      "t2_from_index": 3,
      "t2_to_index": 3,
    },
    {
      "path": ["val2", "val2A"],
      "action": "iterable_items_equal",
      "value": None,
      "old_value": None,
      "type": "<class 'NoneType'>",
      "old_type": "<class 'NoneType'>",
      "new_path": None,
      "t1_from_index": 5,
      "t1_to_index": 7,
      "t2_from_index": 3,
      "t2_to_index": 5,
    },
  ]


def test_diff_pandas():
  @dataclass
  class C:
    data: pd.DataFrame

  s1 = C(data=pd.DataFrame(data={"Strings": ["Hello", "World"]}))
  s2 = C(data=pd.DataFrame(data={"Strings": ["Hello", "Universe"]}))

  assert json.loads(diff_state(s1, s2)) == [
    {
      "path": ["data"],
      "action": "data_frame_changed",
      "value": {
        "__pandas.DataFrame__": '{"schema":{"fields":[{"name":"index","type":"integer"},{"name":"Strings","type":"string"}],"primaryKey":["index"],"pandas_version":"1.4.0"},"data":[{"index":0,"Strings":"Hello"},{"index":1,"Strings":"Universe"}]}'
      },
    }
  ]


def test_diff_nested_pandas():
  @dataclass
  class C:
    data: dict[str, list[pd.DataFrame]]

  s1 = C(data={"test": [pd.DataFrame(data={"Strings": ["Hello", "World"]})]})
  s2 = C(
    data={
      "test": [
        pd.DataFrame(data={"Strings": ["Hello", "Universe"]}),
        pd.DataFrame(data={"Strings": ["Hola", "Universe"]}),
      ]
    }
  )

  assert json.loads(diff_state(s1, s2)) == [
    {
      "path": ["data", "test", 1],
      "action": "iterable_item_added",
      "value": {
        "__pandas.DataFrame__": '{"schema":{"fields":[{"name":"index","type":"integer"},{"name":"Strings","type":"string"}],"primaryKey":["index"],"pandas_version":"1.4.0"},"data":[{"index":0,"Strings":"Hola"},{"index":1,"Strings":"Universe"}]}'
      },
      "old_value": "unknown___",
      "type": "<class 'pandas.core.frame.DataFrame'>",
      "old_type": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
    {
      "path": ["data", "test", 0],
      "action": "data_frame_changed",
      "value": {
        "__pandas.DataFrame__": '{"schema":{"fields":[{"name":"index","type":"integer"},{"name":"Strings","type":"string"}],"primaryKey":["index"],"pandas_version":"1.4.0"},"data":[{"index":0,"Strings":"Hello"},{"index":1,"Strings":"Universe"}]}'
      },
    },
  ]


def test_diff_uploaded_file():
  @dataclass
  class C:
    data: UploadedFile

  s1 = C(data=UploadedFile())
  s2 = C(
    data=UploadedFile(b"data", name="file.png", size=10, mime_type="image/png")
  )

  assert json.loads(diff_state(s1, s2)) == [
    {
      "path": ["data"],
      "action": "mesop_equality_changed",
      "value": {
        "__mesop.UploadedFile__": {
          "contents": "ZGF0YQ==",
          "name": "file.png",
          "size": 10,
          "mime_type": "image/png",
        },
      },
    }
  ]


def test_diff_pydantic_model():
  class PydanticModel(BaseModel):
    name: str = "World"
    counter: int = 0

  @dataclass
  class C:
    data: PydanticModel

  s1 = C(data=PydanticModel())
  s2 = C(data=PydanticModel(name="Hello", counter=1))

  assert json.loads(diff_state(s1, s2)) == [
    {
      "path": ["data"],
      "action": "mesop_equality_changed",
      "value": {
        "__pydantic.BaseModel__": {
          "json": '{"name":"Hello","counter":1}',
          "module": "dataclass_utils.diff_state_test",
          "qualname": "test_diff_pydantic_model.<locals>.PydanticModel",
        },
      },
    }
  ]


def test_diff_uploaded_file_same_no_diff():
  @dataclass
  class C:
    data: UploadedFile

  s1 = C(
    data=UploadedFile(b"data", name="file.png", size=10, mime_type="image/png")
  )
  s2 = C(
    data=UploadedFile(b"data", name="file.png", size=10, mime_type="image/png")
  )

  assert json.loads(diff_state(s1, s2)) == []


def test_diff_set():
  @dataclass
  class C:
    val1: set[int] = field(default_factory=lambda: {1, 2, 3})

  s1 = C()
  s2 = C(val1={1, 5})

  assert json.loads(diff_state(s1, s2)) == [
    {
      "path": ["val1", "__python.set__"],
      "action": "set_item_removed",
      "value": 2,
      "type": "<class 'int'>",
      "old_type": "unknown___",
      "old_value": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
    {
      "path": ["val1", "__python.set__"],
      "action": "set_item_removed",
      "value": 3,
      "type": "<class 'int'>",
      "old_type": "unknown___",
      "old_value": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
    {
      "path": ["val1", "__python.set__"],
      "action": "set_item_added",
      "value": 5,
      "type": "<class 'int'>",
      "old_type": "unknown___",
      "old_value": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
  ]


def test_diff_set_equal():
  @dataclass
  class C:
    val1: set[int] = field(default_factory=lambda: {1, 2, 3})

  s1 = C()
  s2 = C(val1={3, 2, 1})

  assert json.loads(diff_state(s1, s2)) == []


def test_diff_bytes():
  @dataclass
  class C:
    val1: bytes = b"val1"

  s1 = C()
  s2 = C(val1=b"VAL1")

  assert json.loads(diff_state(s1, s2)) == [
    {
      "path": ["val1"],
      "action": "values_changed",
      "value": {
        "__python.bytes__": "VkFMMQ=="
      },  # Check if value is base64 encoded without asserting exact value
      "type": "<class 'bytes'>",
      "old_type": "unknown___",
      "old_value": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    }
  ]


def test_diff_not_dataclass():
  class C:
    val1: set[int] = field(default_factory=lambda: {1, 2, 3})

  with pytest.raises(MesopException):
    diff_state(C(), "s2")

  with pytest.raises(MesopException):
    diff_state("s1", C())


def test_diff_dates():
  @dataclass
  class C:
    val1: set = field(default_factory=set)

  s1 = C()
  s2 = C(
    val1={
      datetime(1972, 2, 2, tzinfo=timezone.utc),
      datetime(2005, 10, 12, tzinfo=timezone(timedelta(hours=-5))),
      datetime(2024, 12, 5, tzinfo=timezone(timedelta(hours=5, minutes=30))),
    }
  )

  assert json.loads(diff_state(s1, s2)) == [
    {
      "path": ["val1", "__python.set__"],
      "action": "set_item_added",
      "value": {"__datetime.datetime__": "2024-12-05T00:00:00+05:30"},
      "type": "<class 'datetime.datetime'>",
      "old_type": "unknown___",
      "old_value": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
    {
      "path": ["val1", "__python.set__"],
      "action": "set_item_added",
      "value": {"__datetime.datetime__": "1972-02-02T00:00:00+00:00"},
      "type": "<class 'datetime.datetime'>",
      "old_type": "unknown___",
      "old_value": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
    {
      "path": ["val1", "__python.set__"],
      "action": "set_item_added",
      "value": {"__datetime.datetime__": "2005-10-12T00:00:00-05:00"},
      "type": "<class 'datetime.datetime'>",
      "old_type": "unknown___",
      "old_value": "unknown___",
      "new_path": None,
      "t1_from_index": None,
      "t1_to_index": None,
      "t2_from_index": None,
      "t2_to_index": None,
    },
  ]


if __name__ == "__main__":
  raise SystemExit(pytest.main([__file__]))
