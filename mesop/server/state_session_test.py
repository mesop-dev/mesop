# ruff: noqa: RUF013
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable
from unittest.mock import patch

import pytest
from google.api_core import gapic_v1
from google.api_core import retry as retries
from google.cloud import firestore
from google.cloud.firestore_v1 import _helpers
from google.cloud.firestore_v1.base_document import DocumentSnapshot
from google.cloud.firestore_v1.collection import CollectionReference
from google.cloud.firestore_v1.document import DocumentReference
from google.cloud.firestore_v1.types import write
from google.protobuf.timestamp_pb2 import Timestamp

from mesop.exceptions import MesopException
from mesop.server.config import Config
from mesop.server.state_session import (
  CreateStateSessionFromConfig,
  FileStateSessionBackend,
  FirestoreStateSessionBackend,
  MemoryStateSessionBackend,
  NullStateSessionBackend,
  SqlStateSessionBackend,
  States,
)


@dataclass
class StateA:
  str_value: str = ""


@dataclass
class StateB:
  int_value: int = 0
  bool_value: bool = True


@pytest.fixture
def sqlite_backend(tmp_path):
  return SqlStateSessionBackend(
    "sqlite:///" + str(tmp_path / "db.sqlite"),
    "mesop_state_session",
  )


@pytest.fixture
def state_session_backend_factory(tmp_path, sqlite_backend):
  """Fixture to provide state session backends for parameterized tests."""
  with patch(
    "mesop.server.state_session.FirestoreStateSessionBackend._initialize_firestore_db",
  ) as _initialize_firestore_db:
    _initialize_firestore_db.return_value = FakeFirestoreClient()
    return {
      "memory": MemoryStateSessionBackend(),
      "file": FileStateSessionBackend(tmp_path),
      "firestore": FirestoreStateSessionBackend("collection"),
      "sql": sqlite_backend,
    }


@pytest.mark.parametrize(
  "backend,expected_backend",
  [
    ("none", NullStateSessionBackend),
    ("memory", MemoryStateSessionBackend),
  ],
)
def test_create_state_session_from_config(backend, expected_backend):
  assert isinstance(
    CreateStateSessionFromConfig(Config(state_session_backend=backend)),
    expected_backend,
  )


def test_create_state_session_file():
  assert isinstance(
    CreateStateSessionFromConfig(
      Config(
        state_session_backend="file",
        state_session_backend_file_base_dir=Path("/tmp"),
      )
    ),
    FileStateSessionBackend,
  )


def test_null_backend_restore_raises_exception():
  backend = NullStateSessionBackend()
  with pytest.raises(
    MesopException, match="No state session backend configured."
  ):
    backend.restore("test", {})


def test_null_backend_save_is_noop():
  backend = NullStateSessionBackend()
  backend.save("test", {})


def test_null_backend_clear_stale_sessions_is_noop():
  backend = NullStateSessionBackend()
  backend.clear_stale_sessions()


@pytest.mark.parametrize("backend_key", ["memory", "file", "firestore", "sql"])
def test_backend_restore_token_not_found_returns_exception(
  backend_key, state_session_backend_factory
):
  backend = state_session_backend_factory[backend_key]
  with pytest.raises(
    MesopException, match="Token not found in state session backend."
  ):
    backend.restore("test", {})


@pytest.mark.parametrize("backend_key", ["memory", "file", "firestore", "sql"])
def test_backend_save_and_restore_states(
  backend_key, state_session_backend_factory
):
  # GIVEN
  backend = state_session_backend_factory[backend_key]
  empty_states: States = {
    type(StateA): StateA(),
    type(StateB): StateB(),
  }
  saved_states: States = {
    type(StateA): StateA(str_value="ABC"),
    type(StateB): StateB(int_value=20, bool_value=False),
  }
  backend = MemoryStateSessionBackend()
  backend.save("test", saved_states)

  # WHEN
  backend.restore("test", empty_states)

  # THEN
  assert empty_states == saved_states


@pytest.mark.parametrize("backend_key", ["memory", "file", "firestore", "sql"])
def test_backend_token_is_cleared_after_restore(
  backend_key, state_session_backend_factory
):
  backend = state_session_backend_factory[backend_key]
  # GIVEN
  empty_states: States = {
    type(StateA): StateA(),
    type(StateB): StateB(),
  }
  saved_states: States = {
    type(StateA): StateA(str_value="ABC"),
    type(StateB): StateB(int_value=20, bool_value=False),
  }
  backend = MemoryStateSessionBackend()
  backend.save("test", saved_states)
  backend.restore("test", empty_states)

  # WHEN / THEN
  with pytest.raises(
    MesopException, match="Token not found in state session backend."
  ):
    backend.restore("test", empty_states)


def test_memory_backend_clear_stale_sessions():
  # GIVEN
  states: States = {
    type(StateA): StateA(str_value="ABC"),
  }
  backend = MemoryStateSessionBackend()
  backend.cache = {
    "key1": (datetime.now() - timedelta(minutes=11), {type(StateA): StateA()}),
    "key2": (datetime.now(), {type(StateA): StateA()}),
    "key3": (datetime.now() - timedelta(minutes=12), {type(StateA): StateA()}),
  }

  # WHEN
  backend.clear_stale_sessions()

  # THEN
  with pytest.raises(
    MesopException, match="Token not found in state session backend."
  ):
    backend.restore("key1", states)
  with pytest.raises(
    MesopException, match="Token not found in state session backend."
  ):
    backend.restore("key3", states)
  backend.restore("key2", states)
  assert states == {type(StateA): StateA()}


@pytest.mark.parametrize(
  "malicious_token",
  [
    "../../../../etc/passwd",
    "../sibling",
    "token/../../escape",
    "token\x00null",
    "token with spaces",
    "",
  ],
)
def test_file_backend_rejects_path_traversal_token(tmp_path, malicious_token):
  backend = FileStateSessionBackend(tmp_path)
  with pytest.raises(MesopException, match="Invalid state token."):
    backend._make_file_path(malicious_token)


def test_file_backend_accepts_valid_token(tmp_path):
  backend = FileStateSessionBackend(tmp_path)
  # token_urlsafe(16) produces base64url characters: A-Z a-z 0-9 _ -
  valid_token = "abcABC123_-XyZ"
  path = backend._make_file_path(valid_token)
  assert path.parent == tmp_path.resolve()


def test_file_backend_clear_stale_sessions_not_stale(tmp_path):
  # GIVEN
  backend = FileStateSessionBackend(tmp_path)
  states: States = {
    type(StateA): StateA(str_value="ABC"),
  }
  backend.save("key1", {type(StateA): StateA()})

  # WHEN
  with patch(
    "mesop.server.state_session._current_datetime",
  ) as _mock_current_datetime:
    _mock_current_datetime.return_value = datetime.now() - timedelta(minutes=15)
    backend.clear_stale_sessions()

    # THEN
    backend.restore("key1", states)
    assert states == {type(StateA): StateA()}


def test_file_backend_clear_stale_sessions(tmp_path):
  # GIVEN
  backend = FileStateSessionBackend(tmp_path)
  states: States = {
    type(StateA): StateA(str_value="ABC"),
  }
  backend.save("key1", {type(StateA): StateA()})
  backend.save("key2", {type(StateA): StateA()})

  # WHEN
  with patch(
    "mesop.server.state_session._current_datetime",
  ) as _mock_current_datetime:
    _mock_current_datetime.return_value = datetime.now() + timedelta(minutes=15)
    backend.clear_stale_sessions()

    # THEN
    with pytest.raises(
      MesopException, match="Token not found in state session backend."
    ):
      backend.restore("key1", states)
    with pytest.raises(
      MesopException, match="Token not found in state session backend."
    ):
      backend.restore("key2", states)


def test_file_backend_clear_stale_sessions_skipped(tmp_path):
  # GIVEN
  backend = FileStateSessionBackend(tmp_path)
  # Force create lock file to test skip behavior.
  backend._can_clear_stale_session()
  empty_states: States = {
    type(StateA): StateA(str_value="ABC"),
  }
  backend.save("key1", {type(StateA): StateA()})

  # WHEN
  with patch(
    "mesop.server.state_session._current_datetime",
  ) as _mock_current_datetime:
    _mock_current_datetime.return_value = datetime.now()
    backend.clear_stale_sessions()

    # THEN
    backend.restore("key1", empty_states)
    assert empty_states == {type(StateA): StateA()}


def test_sql_backend_clear_stale_sessions_not_stale(sqlite_backend):
  # GIVEN
  states: States = {
    type(StateA): StateA(str_value="ABC"),
  }
  sqlite_backend.save("key1", {type(StateA): StateA()})

  # WHEN
  with patch(
    "mesop.server.state_session._current_datetime_utc",
  ) as _mock_current_datetime_utc:
    _mock_current_datetime_utc.return_value = datetime.utcnow() - timedelta(
      minutes=15
    )
    sqlite_backend.request_count = sqlite_backend._SESSION_CLEAR_N_REQUESTS
    sqlite_backend.clear_stale_sessions()

    # THEN
    sqlite_backend.restore("key1", states)
    assert states == {type(StateA): StateA()}


def test_sql_backend_clear_stale_sessions(sqlite_backend):
  # GIVEN
  states: States = {
    type(StateA): StateA(str_value="ABC"),
  }
  sqlite_backend.save("key1", {type(StateA): StateA()})
  sqlite_backend.save("key2", {type(StateA): StateA()})

  # WHEN
  with patch(
    "mesop.server.state_session._current_datetime_utc",
  ) as _mock_current_datetime_utc:
    _mock_current_datetime_utc.return_value = datetime.utcnow() + timedelta(
      minutes=15
    )
    sqlite_backend.request_count = sqlite_backend._SESSION_CLEAR_N_REQUESTS
    sqlite_backend.clear_stale_sessions()

    # THEN
    with pytest.raises(
      MesopException, match="Token not found in state session backend."
    ):
      sqlite_backend.restore("key1", states)
    with pytest.raises(
      MesopException, match="Token not found in state session backend."
    ):
      sqlite_backend.restore("key2", states)


def test_sql_backend_clear_stale_sessions_skipped(sqlite_backend):
  # GIVEN
  states: States = {
    type(StateA): StateA(str_value="ABC"),
  }
  sqlite_backend.save("key1", {type(StateA): StateA()})

  # WHEN
  with patch(
    "mesop.server.state_session._current_datetime_utc",
  ) as _mock_current_datetime_utc:
    _mock_current_datetime_utc.return_value = datetime.utcnow() + timedelta(
      minutes=15
    )
    sqlite_backend.clear_stale_sessions()

    # THEN
    sqlite_backend.restore("key1", states)
    assert states == {type(StateA): StateA()}


# Note: The `FakeFirestoreClient` implementation here ignores a bunch of type checking
# errors since we need to match the parent class method interfaces.


class FakeFirestoreClient(firestore.Client):
  """Fake Firestore client for testing `FirestoreStateSessionBackend`.

  We use a fake since we don't want to make real API calls. This is fairly brittle, but
  covers the basic APIs that we use.

  Ideally, we also include integration tests that use the Firestore emulator.
  """

  def __init__(self):
    self.collections = defaultdict(lambda: FakeFirestoreCollectionReference())  # type: ignore

  def collection(self, *collection_path: str) -> CollectionReference:
    return self.collections[collection_path]  # type: ignore


class FakeFirestoreCollectionReference(CollectionReference):
  def __init__(self):
    self.docs = defaultdict(lambda: FakeFirestoreDocumentReference())

  def document(self, document_id: str | None = None) -> DocumentReference:
    return self.docs[document_id]


class FakeFirestoreDocumentReference(DocumentReference):
  def __init__(self):
    self.doc = DocumentSnapshot(
      self,
      None,
      exists=False,
      read_time=None,
      create_time=None,
      update_time=None,
    )

  def get(
    self,
    field_paths: Iterable[str] = None,  # type: ignore
    transaction=None,
    retry: retries.Retry = gapic_v1.method.DEFAULT,  # type: ignore
    timeout: float = None,  # type: ignore
  ) -> DocumentSnapshot:
    return self.doc

  def set(
    self,
    document_data: dict,
    merge: bool = False,
    retry: retries.Retry = gapic_v1.method.DEFAULT,  # type: ignore
    timeout: float = None,  # type: ignore
  ) -> write.WriteResult:
    self.doc = DocumentSnapshot(
      self,
      document_data,
      exists=True,
      read_time=None,
      create_time=None,
      update_time=None,
    )

    return write.WriteResult()


def delete(
  self,
  option: _helpers.WriteOption = None,  # type: ignore
  retry: retries.Retry = gapic_v1.method.DEFAULT,  # type: ignore
  timeout: float = None,  # type: ignore
) -> Timestamp:
  self.doc = DocumentSnapshot(
    self,
    None,
    exists=False,
    read_time=None,
    create_time=None,
    update_time=None,
  )
  return Timestamp()


if __name__ == "__main__":
  raise SystemExit(pytest.main([__file__]))
