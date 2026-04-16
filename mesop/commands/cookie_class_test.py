"""Unit tests for mesop/commands/cookie_class.py."""

import dataclasses
import json
import os
from unittest.mock import patch

import pytest
from flask import Flask

from mesop.commands.cookie_class import (
  _COOKIE_CLASSES,
  _assert_is_cookieclass,
  _decode_value,
  _encode_value,
  _to_snake_case,
  cookie,
  cookieclass,
)
from mesop.exceptions import MesopDeveloperException

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_flask_app = Flask(__name__)


def _req_ctx(cookies: dict[str, str] | None = None):
  """Return a Flask test request context with the given cookies pre-set."""
  cookie_header = "; ".join(f"{k}={v}" for k, v in (cookies or {}).items())
  headers = {"Cookie": cookie_header} if cookie_header else {}
  return _flask_app.test_request_context("/", headers=headers)


# ---------------------------------------------------------------------------
# _to_snake_case
# ---------------------------------------------------------------------------


def test_to_snake_case_simple():
  assert _to_snake_case("SessionCookie") == "session_cookie"


def test_to_snake_case_already_snake():
  assert _to_snake_case("session_cookie") == "session_cookie"


def test_to_snake_case_acronym():
  assert _to_snake_case("MyHTTPSession") == "my_http_session"


def test_to_snake_case_single_word():
  assert _to_snake_case("Cookie") == "cookie"


def test_to_snake_case_with_digit():
  # Digits behave like lowercase letters: they trigger a split before
  # a following capital, but not after one.
  assert _to_snake_case("Session2Cookie") == "session2_cookie"


def test_to_snake_case_leading_underscore():
  # A leading underscore is preserved; the camelCase transition still fires.
  assert _to_snake_case("_Session") == "__session"


# ---------------------------------------------------------------------------
# @cookieclass decorator
# ---------------------------------------------------------------------------


def test_cookieclass_derives_name_from_class():
  @cookieclass
  class UserPrefs:
    theme: str = "light"

  assert _COOKIE_CLASSES[UserPrefs].name == "user_prefs"


def test_cookieclass_explicit_name():
  @cookieclass(name="my_prefs")
  class AnotherPrefs:
    theme: str = "light"

  assert _COOKIE_CLASSES[AnotherPrefs].name == "my_prefs"


def test_cookieclass_makes_dataclass_if_needed():
  @cookieclass
  class RawClass:
    x: str = ""

  assert dataclasses.is_dataclass(RawClass)


def test_cookieclass_preserves_existing_dataclass():
  @dataclasses.dataclass
  class AlreadyDataclass:
    x: str = ""

  decorated = cookieclass(AlreadyDataclass)
  assert decorated is AlreadyDataclass


def test_cookieclass_signed_flag():
  @cookieclass(signed=True)
  class SignedCookie:
    token: str = ""

  meta = _COOKIE_CLASSES[SignedCookie]
  assert meta.signed is True
  assert meta.encrypted is False


def test_cookieclass_encrypted_flag():
  @cookieclass(encrypted=True)
  class EncCookie:
    token: str = ""

  meta = _COOKIE_CLASSES[EncCookie]
  assert meta.encrypted is True
  assert meta.signed is False


def test_cookieclass_signed_and_encrypted_raises():
  with pytest.raises(MesopDeveloperException, match="mutually exclusive"):

    @cookieclass(signed=True, encrypted=True)
    class Bad:
      x: str = ""


def test_assert_is_cookieclass_raises_for_plain_class():
  class NotACookieClass:
    pass

  with pytest.raises(MesopDeveloperException, match="not a cookieclass"):
    _assert_is_cookieclass(NotACookieClass)


# ---------------------------------------------------------------------------
# me.cookie() — string form (low-level)
# ---------------------------------------------------------------------------


def test_cookie_string_returns_value_when_present():
  with _req_ctx({"my_token": "abc123"}):
    assert cookie("my_token") == "abc123"


def test_cookie_string_returns_empty_when_absent():
  with _req_ctx():
    assert cookie("missing_cookie") == ""


# ---------------------------------------------------------------------------
# me.cookie() — cookieclass form (high-level)
# ---------------------------------------------------------------------------


@cookieclass
class _SessionCookie:
  username: str = ""
  role: str = "guest"


def test_cookie_class_returns_populated_instance():
  name = _COOKIE_CLASSES[_SessionCookie].name
  payload = json.dumps({"username": "alice", "role": "admin"})
  with _req_ctx({name: payload}):
    result = cookie(_SessionCookie)
  assert result.username == "alice"
  assert result.role == "admin"


def test_cookie_class_returns_default_when_absent():
  with _req_ctx():
    result = cookie(_SessionCookie)
  assert result.username == ""
  assert result.role == "guest"


def test_cookie_class_returns_default_on_bad_json():
  name = _COOKIE_CLASSES[_SessionCookie].name
  with _req_ctx({name: "not-valid-json"}):
    result = cookie(_SessionCookie)
  assert result.username == ""


def test_cookie_class_ignores_unknown_fields():
  """Forward-compatibility: extra keys from a newer schema are silently dropped."""
  name = _COOKIE_CLASSES[_SessionCookie].name
  payload = json.dumps(
    {"username": "bob", "role": "guest", "future_field": "ignored"}
  )
  with _req_ctx({name: payload}):
    result = cookie(_SessionCookie)
  assert result.username == "bob"
  assert not hasattr(result, "future_field")


def test_cookie_class_partial_fields():
  """Missing fields should fall back to the dataclass default."""
  name = _COOKIE_CLASSES[_SessionCookie].name
  payload = json.dumps({"username": "carol"})
  with _req_ctx({name: payload}):
    result = cookie(_SessionCookie)
  assert result.username == "carol"
  assert result.role == "guest"


# ---------------------------------------------------------------------------
# Signed cookies — _encode_value / _decode_value
# ---------------------------------------------------------------------------


@cookieclass(signed=True)
class _SignedCookie:
  token: str = ""


def _make_signed_meta():
  return _COOKIE_CLASSES[_SignedCookie]


def test_signed_encode_decode_roundtrip():
  meta = _make_signed_meta()
  with patch.dict(os.environ, {"MESOP_COOKIE_SECRET_KEY": "test-secret-key"}):
    original = json.dumps({"token": "abc"})
    encoded = _encode_value(original, meta)
    assert encoded != original  # value is transformed
    decoded = _decode_value(encoded, meta)
    assert decoded == original


def test_signed_tamper_returns_none():
  meta = _make_signed_meta()
  with patch.dict(os.environ, {"MESOP_COOKIE_SECRET_KEY": "test-secret-key"}):
    encoded = _encode_value(json.dumps({"token": "abc"}), meta)
    tampered = encoded[:-4] + "XXXX"
    assert _decode_value(tampered, meta) is None


def test_signed_wrong_key_returns_none():
  meta = _make_signed_meta()
  with patch.dict(os.environ, {"MESOP_COOKIE_SECRET_KEY": "key-a"}):
    encoded = _encode_value(json.dumps({"token": "abc"}), meta)
  with patch.dict(os.environ, {"MESOP_COOKIE_SECRET_KEY": "key-b"}):
    assert _decode_value(encoded, meta) is None


def test_signed_cookie_read_discards_tampered_value():
  """me.cookie() should return a default instance when the signature fails."""
  meta = _make_signed_meta()
  with patch.dict(os.environ, {"MESOP_COOKIE_SECRET_KEY": "key-a"}):
    encoded = _encode_value(json.dumps({"token": "real"}), meta)
  tampered_cookie = {_COOKIE_CLASSES[_SignedCookie].name: encoded}
  with _req_ctx(tampered_cookie):
    with patch.dict(os.environ, {"MESOP_COOKIE_SECRET_KEY": "key-b"}):
      result = cookie(_SignedCookie)
  assert result.token == ""


def test_signed_missing_secret_key_raises():
  meta = _make_signed_meta()
  with patch.dict(os.environ, {"MESOP_COOKIE_SECRET_KEY": ""}):
    with pytest.raises(
      MesopDeveloperException, match="MESOP_COOKIE_SECRET_KEY"
    ):
      _encode_value(json.dumps({"token": "abc"}), meta)


# ---------------------------------------------------------------------------
# Encrypted cookies
# ---------------------------------------------------------------------------


def test_encrypted_encode_decode_roundtrip():
  pytest.importorskip("cryptography")

  @cookieclass(encrypted=True)
  class _EncCookie:
    secret: str = ""

  meta = _COOKIE_CLASSES[_EncCookie]
  with patch.dict(os.environ, {"MESOP_COOKIE_SECRET_KEY": "test-secret-key"}):
    original = json.dumps({"secret": "hidden"})
    encoded = _encode_value(original, meta)
    assert encoded != original
    decoded = _decode_value(encoded, meta)
    assert decoded == original


def test_encrypted_tamper_returns_none():
  pytest.importorskip("cryptography")

  @cookieclass(encrypted=True)
  class _EncCookie2:
    secret: str = ""

  meta = _COOKIE_CLASSES[_EncCookie2]
  with patch.dict(os.environ, {"MESOP_COOKIE_SECRET_KEY": "test-secret-key"}):
    assert _decode_value("not-valid-fernet-token", meta) is None


if __name__ == "__main__":
  raise SystemExit(pytest.main([__file__, "-v"]))
