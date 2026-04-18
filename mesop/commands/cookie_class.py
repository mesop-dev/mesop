"""cookieclass — structured-data cookie API for Mesop.

Usage::

    @me.cookieclass
    class SessionCookie:
        username: str = ""
        role: str = "guest"

    # In on_load: read cookies sent by the browser.
    session = me.cookie(SessionCookie)

    # In an event handler: write/update the cookie.
    me.set_cookie(SessionCookie(username="alice", role="admin"), max_age=3600)

    # Delete the cookie.
    me.delete_cookie(SessionCookie)

Signed cookies (tamper-proof, contents readable)::

    @me.cookieclass(signed=True)
    class SessionCookie:
        username: str = ""

Encrypted cookies (tamper-proof, contents hidden)::

    @me.cookieclass(encrypted=True)
    class SessionCookie:
        username: str = ""

"""

from __future__ import annotations

import dataclasses
import json
import re
from collections.abc import Callable
from typing import Any, TypeVar, overload

from mesop.dataclass_utils import dataclass_with_defaults
from mesop.exceptions import MesopDeveloperException

T = TypeVar("T")


@dataclasses.dataclass
class _CookieClassMeta:
  name: str
  signed: bool
  encrypted: bool


# Maps cookieclass types → metadata.
_COOKIE_CLASSES: dict[type, _CookieClassMeta] = {}


# ---------------------------------------------------------------------------
# Public decorator
# ---------------------------------------------------------------------------


@overload
def cookieclass(cls: type[T]) -> type[T]: ...


@overload
def cookieclass(
  cls: None = None,
  *,
  name: str | None = None,
  signed: bool = False,
  encrypted: bool = False,
) -> Callable[[type[T]], type[T]]: ...  # type: ignore[misc]


def cookieclass(
  cls: type[T] | None = None,
  *,
  name: str | None = None,
  signed: bool = False,
  encrypted: bool = False,
) -> type[T] | Callable[[type[T]], type[T]]:
  """Decorator that marks a dataclass as a cookie-backed structured store.

  !!! warning "Experimental"
      This API is experimental and may change in future releases.

  The class is automatically turned into a ``dataclass`` if it is not already
  one.  All fields must have JSON-serialisable types (``str``, ``int``,
  ``float``, ``bool``, ``None``, or nested combinations thereof).

  The cookie name defaults to the snake_case version of the class name.
  Override it with the optional ``name`` keyword argument.

  Requires ``MESOP_COOKIE_SECRET_KEY`` to be set.

  **Signed cookies** (``signed=True``) add an HMAC to the cookie value so
  any tampering is detected on read.  The contents are still Base64-visible
  in DevTools.

  **Encrypted cookies** (``encrypted=True``) use Fernet symmetric encryption
  so the contents are completely hidden.  Requires the ``cryptography``
  package (``pip install cryptography``).

  ``signed`` and ``encrypted`` are mutually exclusive.

  Args:
    cls: The class to decorate (used when the decorator is applied without
      parentheses, e.g. ``@me.cookieclass``).
    name: Explicit cookie name.  Defaults to snake_case of the class name.
    signed: When ``True``, the serialised value is HMAC-signed so tampering
      is detected.
    encrypted: When ``True``, the serialised value is Fernet-encrypted.
      Requires ``pip install cryptography``.

  Returns:
    The decorated class (registered as a cookieclass and ensured to be a
    ``dataclass``).
  """
  if signed and encrypted:
    raise MesopDeveloperException(
      "cookieclass: 'signed' and 'encrypted' are mutually exclusive. "
      "Use 'encrypted=True' alone — it already implies integrity protection."
    )

  def decorator(c: type[T]) -> type[T]:
    # dataclass_with_defaults ensures every field has a default value so
    # that cls() can always be called without arguments — this is required
    # by me.cookie() which falls back to a default instance when the cookie
    # is absent or unparseable.
    c = dataclass_with_defaults(c)
    cookie_name = name if name is not None else _to_snake_case(c.__name__)
    _COOKIE_CLASSES[c] = _CookieClassMeta(
      name=cookie_name, signed=signed, encrypted=encrypted
    )
    return c

  if cls is not None:
    # Called as @me.cookieclass (no parentheses).
    return decorator(cls)
  # Called as @me.cookieclass(...) (with parentheses).
  return decorator


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


@overload
def cookie(cls: str) -> str: ...


@overload
def cookie(cls: type[T]) -> T: ...


def cookie(cls: type[T] | str) -> T | str:
  """Read a cookie from the current request's cookies.

  !!! warning "Experimental"
      This API is experimental and may change in future releases.

  **Two call forms:**

  **High-level** — pass a ``@me.cookieclass`` type to get a typed instance.
  If the cookie is absent, fails signature verification, or cannot be parsed,
  a fresh instance with all default field values is returned — no exception
  is raised.

  .. code-block:: python

      session = me.cookie(SessionCookie)   # returns a SessionCookie instance

  **Low-level** — pass a plain string cookie name to get the raw value.
  Returns an empty string ``""`` if the cookie is absent.

  .. code-block:: python

      token = me.cookie("session_id")      # returns str

  Args:
    cls: A ``@me.cookieclass``-decorated class (high-level), or a plain
      ``str`` cookie name (low-level).

  Returns:
    A populated instance of *cls* (high-level) or a raw ``str`` (low-level).
  """
  if isinstance(cls, str):
    return _get_request_cookie(cls)

  _assert_is_cookieclass(cls)
  meta = _COOKIE_CLASSES[cls]

  raw = _get_request_cookie(meta.name)
  if not raw:
    return cls()  # type: ignore[call-arg]

  decoded = _decode_value(raw, meta)
  if decoded is None:
    return cls()  # type: ignore[call-arg]

  try:
    data: dict[str, Any] = json.loads(decoded)
  except (json.JSONDecodeError, ValueError):
    return cls()  # type: ignore[call-arg]

  # Build the instance, ignoring unknown keys (forward-compatibility).
  known = {f.name for f in dataclasses.fields(cls)}  # type: ignore[arg-type]
  filtered = {k: v for k, v in data.items() if k in known}
  return cls(**filtered)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Internal helpers — cookie encoding / decoding
# ---------------------------------------------------------------------------


def _encode_value(json_str: str, meta: _CookieClassMeta) -> str:
  """Return the cookie value to store, applying signing or encryption."""
  if meta.encrypted:
    return _fernet_encrypt(json_str, _get_secret_key())
  if meta.signed:
    return _itsdangerous_sign(json_str, meta.name, _get_secret_key())
  return json_str


def _decode_value(raw: str, meta: _CookieClassMeta) -> str | None:
  """Reverse of ``_encode_value``.  Returns ``None`` on verification failure."""
  if meta.encrypted:
    return _fernet_decrypt(raw, _get_secret_key())
  if meta.signed:
    return _itsdangerous_unsign(raw, meta.name, _get_secret_key())
  return raw


def _get_secret_key() -> str:
  """Return MESOP_COOKIE_SECRET_KEY, raising a helpful error if unset."""
  import os

  key = os.environ.get("MESOP_COOKIE_SECRET_KEY", "")
  if not key:
    raise MesopDeveloperException(
      "MESOP_COOKIE_SECRET_KEY must be set to use Mesop cookies.\n"
      "Set it as an environment variable before starting Mesop:\n"
      "  MESOP_COOKIE_SECRET_KEY=<your-secret> mesop main.py\n"
      "Generate a strong key with:\n"
      '  python -c "import secrets; print(secrets.token_hex(32))"'
    )
  return key


def _itsdangerous_sign(value: str, salt: str, secret_key: str) -> str:
  from itsdangerous import URLSafeSerializer

  return URLSafeSerializer(secret_key, salt=f"mesop-cookie-{salt}").dumps(value)


def _itsdangerous_unsign(value: str, salt: str, secret_key: str) -> str | None:
  from itsdangerous import BadSignature, URLSafeSerializer

  try:
    return URLSafeSerializer(secret_key, salt=f"mesop-cookie-{salt}").loads(
      value
    )
  except BadSignature:
    return None


def _fernet_encrypt(value: str, secret_key: str) -> str:
  try:
    from cryptography.fernet import Fernet
  except ImportError as exc:
    raise MesopDeveloperException(
      "encrypted=True requires the 'cryptography' package.\n"
      "Install it with: pip install cryptography"
    ) from exc

  import base64
  import hashlib

  key = base64.urlsafe_b64encode(hashlib.sha256(secret_key.encode()).digest())
  return Fernet(key).encrypt(value.encode()).decode()


def _fernet_decrypt(value: str, secret_key: str) -> str | None:
  try:
    from cryptography.fernet import Fernet, InvalidToken
  except ImportError as exc:
    raise MesopDeveloperException(
      "encrypted=True requires the 'cryptography' package.\n"
      "Install it with: pip install cryptography"
    ) from exc

  import base64
  import hashlib

  key = base64.urlsafe_b64encode(hashlib.sha256(secret_key.encode()).digest())
  try:
    return Fernet(key).decrypt(value.encode()).decode()
  except (InvalidToken, Exception):
    return None


# ---------------------------------------------------------------------------
# Internal helpers — misc
# ---------------------------------------------------------------------------


def _to_snake_case(name: str) -> str:
  """Convert CamelCase to snake_case."""
  s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
  return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _assert_is_cookieclass(cls: type) -> None:
  if cls not in _COOKIE_CLASSES:
    raise MesopDeveloperException(
      f"`{cls.__name__}` is not a cookieclass. "
      "Did you forget to decorate it with @me.cookieclass?"
    )


def _get_request_cookie(name: str) -> str:
  """Return the raw cookie string from the current Flask request, or ''."""
  try:
    from flask import request

    return request.cookies.get(name, "")
  except RuntimeError:
    # Outside a Flask request context (e.g., tests).
    return ""
