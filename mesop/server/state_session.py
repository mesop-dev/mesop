import logging
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Protocol

import msgpack

from mesop.dataclass_utils import (
  serialize_dataclass,
  update_dataclass_from_json,
)
from mesop.exceptions import MesopException
from mesop.server.config import Config, app_config

States = dict[type[Any], object]


def _current_datetime():
  """Helper to return datetime now so we can mock the time easier."""
  return datetime.now()


def _current_datetime_utc():
  """Helper to return datetime utc now so we can mock the time easier."""
  return datetime.utcnow()


class StateSessionBackend(Protocol):
  """Interface for state session backends."""

  def restore(self, token: str, states: States):
    """Gets the saved state from the given token and updates the given state."""
    raise NotImplementedError()

  def save(self, token: str, states: States):
    """Saves state to the backend with the given token."""
    raise NotImplementedError()

  def clear_stale_sessions(self):
    """Deletes unused state data."""
    raise NotImplementedError()


class NullStateSessionBackend(StateSessionBackend):
  """State session backend used when state sessions are disabled."""

  def restore(self, token: str, states: States):
    raise MesopException("No state session backend configured.")

  def save(self, token: str, states: States):
    pass

  def clear_stale_sessions(self):
    pass


class MemoryStateSessionBackend(StateSessionBackend):
  """Stores state in memory.

  The main limitation of this backend is that deloyments with multiple processes /
  replicas / instances will cause a lot of cache misses if there is no session affinity.

  This is because memory is local to each Mesop server process.

  In addition, memory should be allocated carefully to the amount of traffic and state
  size that will be expected by the Mesop app.
  """

  # Hardcode for now, but probably make adjustable in the future.
  _SESSION_TTL_MINUTES = 10

  def __init__(self):
    self.cache = {}
    self.last_checked_sessions = datetime(1900, 1, 1)

  def restore(self, token: str, states: States):
    if token not in self.cache:
      raise MesopException("Token not found in state session backend.")
    _, cached_states = self.cache[token]
    for key, cached_state in cached_states.items():
      states[key] = cached_state

    # Delete the cache instance each time since a temporary state may be used.
    del self.cache[token]

  def save(self, token: str, states: States):
    self.cache[token] = (_current_datetime(), states)

  def clear_stale_sessions(self):
    stale_keys = set()

    # Avoid trying to clear sessions with every request to avoid unnecessary processing.
    current_time = _current_datetime()
    if (
      self.last_checked_sessions + timedelta(minutes=self._SESSION_TTL_MINUTES)
      > current_time
    ):
      return

    self.last_checked_sessions = current_time

    # Copy cache keys first to avoid possibility of the keys being removed
    # while processing stale keys.
    cache_keys = list(self.cache)

    for key in cache_keys:
      timestamp, _ = self.cache.get(key, (None, None))
      if (
        timestamp
        and timestamp + timedelta(minutes=self._SESSION_TTL_MINUTES)
        < current_time
      ):
        stale_keys.add(key)

    for key in stale_keys:
      try:
        del self.cache[key]
      except KeyError:
        logging.warning(
          f"Tried to delete non-existent memory cache entry {key}."
        )


class FileStateSessionBackend(StateSessionBackend):
  """Stores state on the filesystem.

  This backend allows state to be shared across processes on the same server. If session
  affinity is not available, then the only way to improve performance is to scale
  vertically.

  The main bottleneck is disk read/write performance. If using this backend, you should
  load test against expected traffic and state size to see if this backend meets your
  needs.
  """

  # Hardcode for now, but probably make adjustable in the future.
  _SESSION_TTL_MINUTES = 10
  _SESSION_LOCK_FILE = "mesop_session.lock"

  def __init__(self, base_dir: Path):
    if base_dir is None:
      raise RuntimeError(
        "Base dir must be set when using `FileStateSessionBackend`"
      )
    self.base_dir = base_dir
    self.prefix = "session"

  # Matches tokens produced by secrets.token_urlsafe: base64url alphabet only.
  _VALID_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]+$")

  def _make_file_path(self, token: str) -> Path:
    if not self._VALID_TOKEN_RE.match(token):
      raise MesopException("Invalid state token.")
    file_path = (self.base_dir / (self.prefix + token)).resolve()
    if not file_path.is_relative_to(self.base_dir.resolve()):
      raise MesopException("Invalid state token.")
    return file_path

  def restore(self, token: str, states: States):
    """Gets the saved state from the given token and updates the given state."""
    file_path = self._make_file_path(token)
    try:
      with open(file_path, "rb") as f:
        states_data = msgpack.unpackb(f.read())
      _deserialize_state(states, states_data)
    except FileNotFoundError as e:
      raise MesopException("Token not found in state session backend.") from e
    else:
      try:
        os.remove(file_path)
      except FileNotFoundError as e:
        logging.warning("Failed to delete file after restore - " + str(e))

  def save(self, token: str, states: States):
    """Saves state to the backend with the given token."""
    with open(self._make_file_path(token), "wb") as f:
      f.write(msgpack.packb(_serialize_state(states)))  # type: ignore

  def clear_stale_sessions(self):
    """Deletes unused state data."""
    if not self._can_clear_stale_session():
      return

    for filename in os.listdir(self.base_dir):
      file_path = self.base_dir / filename
      current_time = _current_datetime()
      if os.path.isfile(file_path) and filename.startswith(self.prefix):
        timestamp = datetime.fromtimestamp(os.path.getctime(file_path))
        if (
          timestamp + timedelta(minutes=self._SESSION_TTL_MINUTES)
          < current_time
        ):
          try:
            os.remove(file_path)
          except FileNotFoundError as e:
            logging.warning(
              "Failed to delete file while clearing sessions - " + str(e)
            )

  def _can_clear_stale_session(self):
    """Check if we should try to clean up stale sessions.

    We do not want to clear file sessions after every request, so we will limit attempts
    to every `_SESSION_TTL_MINUTES`.

    This does not prevent the possibility of multiple concurrent deletions, but that
    is fine. We will just ignore the deletion errors in those scenarios.
    """
    lock_file_path = self.base_dir / self._SESSION_LOCK_FILE
    if os.path.isfile(lock_file_path):
      current_time = _current_datetime()
      timestamp = datetime.fromtimestamp(os.path.getmtime(lock_file_path))
      if (
        timestamp + timedelta(minutes=self._SESSION_TTL_MINUTES) > current_time
      ):
        return False

    # Update modification time.
    with open(lock_file_path, "a"):
      os.utime(lock_file_path, None)

    return True


class FirestoreStateSessionBackend(StateSessionBackend):
  """State session backend using GCP Firestore."""

  # Hardcode for now, but probably make adjustable in the future.
  _SESSION_TTL_MINUTES = 10

  def __init__(self, collection_name: str):
    self.collection_name = collection_name
    self.db = self._initialize_firestore_db()

  def _initialize_firestore_db(self):
    logging.warning(
      "You need to manually create a TTL policy on your Firestore to clear out stale\n"
      "session data. Otherwise, you will exceed the 1GB free storage allowance.\n\n"
      "You can create a TTL policy by running this command: \n\n"
      f"  gcloud firestore fields ttls update expiresAt --collection-group={self.collection_name}\n\n"
    )
    # Lazy load Firestore dependencies since it is not a core functionality.
    import firebase_admin
    from firebase_admin import firestore

    # This uses the application default credentials (ADC) which are set by default on
    # GCP services, such as Cloud Run.
    #
    # For local development, you will need to initialize the ADC using this command:
    #
    #   gcloud auth application-default login
    #
    # If you have multiple GCP projects, you may need to update the project associated
    # with the ADC:
    #
    #   GCP_PROJECT=gcp-project
    #   gcloud config set project $GCP_PROJECT
    #   gcloud auth application-default set-quota-project $GCP_PROJECT
    firebase_admin.initialize_app()
    # We use the default Firestore database associated with the ADC project.
    return firestore.client()

  def restore(self, token: str, states: States):
    """Gets the saved state from the given token and updates the given state."""
    doc_ref = self.db.collection(self.collection_name).document(token)
    doc = doc_ref.get()

    if not doc.exists:
      raise MesopException("Token not found in state session backend.")

    states_data = msgpack.unpackb(doc.to_dict()["state"])  # type: ignore
    _deserialize_state(states, states_data)

    doc_ref.delete()

  def save(self, token: str, states: States):
    """Saves state to the backend with the given token."""
    doc_ref = self.db.collection(self.collection_name).document(token)
    doc_ref.set(
      {
        "state": msgpack.packb(_serialize_state(states)),
        "expiresAt": _current_datetime_utc()
        + timedelta(minutes=self._SESSION_TTL_MINUTES),
      }
    )

  def clear_stale_sessions(self):
    """Deletes unused state data.

    In Firestore, you can set TTLs to delete stale data,
    so this method is a noop.

    The command to enable a TTL policy is:

      COLLECTION_NAME=collection_name
      gcloud firestore fields ttls update expiresAt \
        --collection-group=$COLLECTION_NAME
    """
    pass


class SqlStateSessionBackend(StateSessionBackend):
  """State session backend using SQL via SQL Alchemy."""

  # Hardcode for now, but probably make adjustable in the future.
  _SESSION_TTL_MINUTES = 10
  _SESSION_CLEAR_N_REQUESTS = 10

  def __init__(self, connection_uri: str, table_name: str):
    from sqlalchemy import (
      Column,
      DateTime,
      LargeBinary,
      MetaData,
      String,
      Table,
      create_engine,
    )

    self.db = create_engine(connection_uri)
    self.metadata = MetaData()
    self.table = Table(
      table_name,
      self.metadata,
      Column("token", String(23), primary_key=True),
      Column("states", LargeBinary, nullable=False),
      Column("created_at", DateTime, nullable=False, index=True),
    )
    # Tries to create the database if it does not exist. Outside of SQLite3, the user
    # will need to manually create the database table since the database user should
    # generally have the minimum necessary privileges.
    #
    # If the table does not exist and cannot be created a sqlalchemy.exc.ProgrammingError
    # error will be raised.
    self.metadata.create_all(self.db)

    # We will count each restore call as a request. This is used for tracking when we
    # should clear stale database sessions.
    self.request_count = 0

  def restore(self, token: str, states: States):
    from sqlalchemy import delete, select

    self.request_count += 1

    with self.db.connect() as conn:
      result = conn.execute(
        select(self.table).where(self.table.c.token == token)
      ).one_or_none()
      if result:
        states_data = msgpack.unpackb(result.states)  # type: ignore
        _deserialize_state(states, states_data)
      else:
        raise MesopException("Token not found in state session backend.")

    with self.db.begin() as conn:
      conn.execute(delete(self.table).where(self.table.c.token == token))

  def save(self, token: str, states: States):
    from sqlalchemy import insert

    with self.db.begin() as conn:
      conn.execute(
        insert(self.table).values(
          token=token,
          states=msgpack.packb(_serialize_state(states)),
          created_at=_current_datetime_utc(),
        )
      )

  def clear_stale_sessions(self):
    """Clears stale sessions from database.

    Only query the database after every X requests to avoid fruitlessly querying the
    database unnecessarily.
    """
    from sqlalchemy import delete

    if self.request_count < self._SESSION_CLEAR_N_REQUESTS:
      return

    self.request_count = 0

    with self.db.begin() as conn:
      conn.execute(
        delete(self.table).where(
          self.table.c.created_at
          < _current_datetime_utc()
          - timedelta(minutes=self._SESSION_TTL_MINUTES)
        )
      )


def CreateStateSessionFromConfig(config: Config):
  """Factory function to state session backend."""
  if config.state_session_backend == "memory":
    return MemoryStateSessionBackend()
  elif config.state_session_backend == "file":
    return FileStateSessionBackend(config.state_session_backend_file_base_dir)
  elif config.state_session_backend == "firestore":
    return FirestoreStateSessionBackend(
      config.state_session_backend_firestore_collection
    )
  elif config.state_session_backend == "sql":
    return SqlStateSessionBackend(
      config.state_session_backend_sql_connection_uri,
      config.state_session_backend_sql_table,
    )
  return NullStateSessionBackend()


# The state session is a singleton object.
state_session = CreateStateSessionFromConfig(app_config)


def _serialize_state(states: States) -> list[str]:
  states_data = []
  for state in states.values():
    states_data.append(serialize_dataclass(state))
  return states_data


def _deserialize_state(states: States, states_data: list[str]):
  for state, serialized_state in zip(states.values(), states_data):
    update_dataclass_from_json(state, serialized_state)
