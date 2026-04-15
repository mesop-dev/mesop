"""Unit tests for mesop/commands/set_cookie.py."""

import dataclasses
import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from mesop.commands.cookie_class import _COOKIE_CLASSES, cookieclass
from mesop.commands.set_cookie import _resolve_secure, delete_cookie, set_cookie
from mesop.exceptions import MesopDeveloperException

_flask_app = Flask(__name__)


def _req_ctx(secure: bool = False):
  scheme = "https" if secure else "http"
  return _flask_app.test_request_context("/", base_url=f"{scheme}://localhost/")


# ---------------------------------------------------------------------------
# _resolve_secure
# ---------------------------------------------------------------------------


def test_resolve_secure_true():
  assert _resolve_secure(True) is True


def test_resolve_secure_false():
  assert _resolve_secure(False) is False


def test_resolve_secure_none_on_http():
  with _req_ctx(secure=False):
    assert _resolve_secure(None) is False


def test_resolve_secure_none_on_https():
  with _req_ctx(secure=True):
    assert _resolve_secure(None) is True


def test_resolve_secure_none_outside_request():
  # Outside a Flask request context (e.g. cold import) defaults to False.
  assert _resolve_secure(None) is False


# ---------------------------------------------------------------------------
# set_cookie — string form
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_context():
  ctx = MagicMock()
  with patch("mesop.commands.set_cookie.runtime") as mock_rt:
    mock_rt.return_value.context.return_value = ctx
    yield ctx


def test_set_cookie_string_calls_context(mock_context):
  with _req_ctx():
    set_cookie("session_id", "abc123", max_age=3600)

  mock_context.set_cookie.assert_called_once_with(
    "session_id",
    "abc123",
    max_age=3600,
    path="/",
    domain=None,
    secure=False,  # http → False via _resolve_secure(None)
    httponly=True,
    samesite="Lax",
  )


def test_set_cookie_string_explicit_secure(mock_context):
  with _req_ctx():
    set_cookie("tok", "val", secure=True)

  _, kwargs = mock_context.set_cookie.call_args
  assert kwargs["secure"] is True


def test_set_cookie_string_missing_value_raises():
  with pytest.raises(TypeError, match="requires a value"):
    set_cookie("session_id")


# ---------------------------------------------------------------------------
# set_cookie — cookieclass form
# ---------------------------------------------------------------------------


@cookieclass
@dataclasses.dataclass
class _Prefs:
  theme: str = "light"
  font_size: int = 14


def test_set_cookie_instance_serialises_to_json(mock_context):
  with _req_ctx():
    set_cookie(_Prefs(theme="dark", font_size=16))

  name, value = mock_context.set_cookie.call_args[0]
  assert name == _COOKIE_CLASSES[_Prefs].name
  assert json.loads(value) == {"theme": "dark", "font_size": 16}


def test_set_cookie_instance_forwards_kwargs(mock_context):
  with _req_ctx():
    set_cookie(_Prefs(), max_age=7200, httponly=False, samesite="Strict")

  _, kwargs = mock_context.set_cookie.call_args
  assert kwargs["max_age"] == 7200
  assert kwargs["httponly"] is False
  assert kwargs["samesite"] == "Strict"


def test_set_cookie_non_cookieclass_raises(mock_context):
  class NotRegistered:
    pass

  with pytest.raises(MesopDeveloperException, match="not a cookieclass"):
    set_cookie(NotRegistered())


# ---------------------------------------------------------------------------
# delete_cookie — string form
# ---------------------------------------------------------------------------


def test_delete_cookie_string(mock_context):
  # secure=None outside a request context resolves to False.
  delete_cookie("session_id")
  mock_context.delete_cookie.assert_called_once_with(
    "session_id", path="/", domain=None, secure=False
  )


def test_delete_cookie_string_with_path(mock_context):
  delete_cookie("session_id", path="/app", domain="example.com")
  mock_context.delete_cookie.assert_called_once_with(
    "session_id", path="/app", domain="example.com", secure=False
  )


def test_delete_cookie_secure_auto_detected_on_https(mock_context):
  with _req_ctx(secure=True):
    delete_cookie("session_id")
  mock_context.delete_cookie.assert_called_once_with(
    "session_id", path="/", domain=None, secure=True
  )


# ---------------------------------------------------------------------------
# delete_cookie — cookieclass form
# ---------------------------------------------------------------------------


@cookieclass
@dataclasses.dataclass
class _Session:
  username: str = ""


def test_delete_cookie_class(mock_context):
  delete_cookie(_Session)
  mock_context.delete_cookie.assert_called_once_with(
    _COOKIE_CLASSES[_Session].name, path="/", domain=None, secure=False
  )


def test_delete_cookie_non_cookieclass_raises(mock_context):
  class NotRegistered:
    pass

  with pytest.raises(MesopDeveloperException, match="not a cookieclass"):
    delete_cookie(NotRegistered)


if __name__ == "__main__":
  raise SystemExit(pytest.main([__file__, "-v"]))
