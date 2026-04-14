"""cookieclass — structured-data cookie API for Mesop.

Usage::

    @me.cookieclass
    class SessionCookie:
        username: str = ""
        role: str = "guest"

    # In on_load: read cookies sent by the browser.
    session = me.cookie(SessionCookie)

    # In an event handler: write/update the cookie.
    me.save_cookie(SessionCookie(username="alice", role="admin"), max_age=3600)

    # Delete the cookie.
    me.delete_cookie(SessionCookie)
"""

from __future__ import annotations

import dataclasses
import json
import re
from typing import Any, Type, TypeVar, overload

from mesop.exceptions import MesopDeveloperException

T = TypeVar("T")

# Maps cookieclass types → their cookie name.
_COOKIE_CLASSES: dict[type, str] = {}


# ---------------------------------------------------------------------------
# Public decorator
# ---------------------------------------------------------------------------


@overload
def cookieclass(cls: type[T]) -> type[T]: ...


@overload
def cookieclass(
  *, name: str | None = None
) -> "Callable[[type[T]], type[T]]": ...  # type: ignore[name-defined]


def cookieclass(cls: type[T] | None = None, *, name: str | None = None):
  """Decorator that marks a dataclass as a cookie-backed structured store.

  !!! warning "Experimental"
      This API is experimental and may change in future releases.

  The class is automatically turned into a ``dataclass`` if it is not already
  one.  All fields must have JSON-serialisable types (``str``, ``int``,
  ``float``, ``bool``, ``None``, or nested combinations thereof).

  The cookie name defaults to the snake_case version of the class name.
  Override it with the optional ``name`` keyword argument::

      @me.cookieclass(name="my_session")
      class SessionCookie:
          username: str = ""

  Args:
    cls: The class to decorate (used when the decorator is applied without
      parentheses, e.g. ``@me.cookieclass``).
    name: Explicit cookie name.  Defaults to snake_case of the class name.

  Returns:
    The decorated class (unchanged except for being registered as a
    cookieclass and ensured to be a ``dataclass``).
  """

  def decorator(c: type[T]) -> type[T]:
    if not dataclasses.is_dataclass(c):
      c = dataclasses.dataclass(c)
    cookie_name = name if name is not None else _to_snake_case(c.__name__)
    _COOKIE_CLASSES[c] = cookie_name
    return c

  if cls is not None:
    # Called as @me.cookieclass (no parentheses).
    return decorator(cls)
  # Called as @me.cookieclass(...) (with parentheses).
  return decorator


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def cookie(cls: type[T]) -> T:
  """Read a cookieclass instance from the current request's cookies.

  !!! warning "Experimental"
      This API is experimental and may change in future releases.

  If the cookie is absent or its value cannot be parsed, a fresh instance
  with all default field values is returned — no exception is raised.

  Args:
    cls: A class decorated with ``@me.cookieclass``.

  Returns:
    A populated instance of *cls*.
  """
  _assert_is_cookieclass(cls)
  cookie_name = _COOKIE_CLASSES[cls]

  raw = _get_request_cookie(cookie_name)
  if not raw:
    return cls()  # type: ignore[call-arg]

  try:
    data: dict[str, Any] = json.loads(raw)
  except (json.JSONDecodeError, ValueError):
    return cls()  # type: ignore[call-arg]

  # Build the instance, ignoring unknown keys (forward-compatibility).
  known = {f.name for f in dataclasses.fields(cls)}  # type: ignore[arg-type]
  filtered = {k: v for k, v in data.items() if k in known}
  return cls(**filtered)  # type: ignore[call-arg]


def save_cookie(
  instance: Any,
  *,
  max_age: int | None = None,
  path: str = "/",
  domain: str | None = None,
  secure: bool | None = None,
  httponly: bool = True,
  samesite: str = "Lax",
) -> None:
  """Persist a cookieclass instance as a browser cookie.

  !!! warning "Experimental"
      This API is experimental and may change in future releases.

  The instance is JSON-serialised and stored under the cookie name derived
  from its class.  Call this inside an event handler (or ``on_load``).

  Args:
    instance: An instance of a ``@me.cookieclass``-decorated class.
    max_age: Cookie lifetime in seconds.  ``None`` (default) creates a
      session cookie.
    path: URL path scope.  Defaults to ``"/"``.
    domain: Domain scope.  ``None`` means the current domain.
    secure: When ``True``, cookie is HTTPS-only.  When ``None`` (default),
      auto-detects from the current request (``True`` on HTTPS, ``False``
      on HTTP — useful for local development).
    httponly: Prevent JavaScript from accessing the cookie.  Defaults to
      ``True``.
    samesite: ``"Lax"`` (default), ``"Strict"``, or ``"None"``.
  """
  cls = type(instance)
  _assert_is_cookieclass(cls)
  cookie_name = _COOKIE_CLASSES[cls]

  resolved_secure = _resolve_secure(secure)

  # Lazy import to avoid circular deps at module-import time.
  from mesop.runtime import runtime

  runtime().context().set_cookie(
    cookie_name,
    json.dumps(dataclasses.asdict(instance)),
    max_age=max_age,
    path=path,
    domain=domain,
    secure=resolved_secure,
    httponly=httponly,
    samesite=samesite,
  )


def delete_cookieclass(
  cls: type,
  *,
  path: str = "/",
  domain: str | None = None,
) -> None:
  """Delete the browser cookie associated with a cookieclass.

  !!! warning "Experimental"
      This API is experimental and may change in future releases.

  This is the cookieclass-aware counterpart of ``me.delete_cookie()``.
  It looks up the cookie name automatically from the registered class.

  Args:
    cls: A class decorated with ``@me.cookieclass``.
    path: Must match the ``path`` used when the cookie was created.
    domain: Must match the ``domain`` used when the cookie was created.
  """
  _assert_is_cookieclass(cls)
  cookie_name = _COOKIE_CLASSES[cls]
  from mesop.runtime import runtime

  runtime().context().delete_cookie(cookie_name, path=path, domain=domain)


# ---------------------------------------------------------------------------
# Internal helpers
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


def _resolve_secure(secure: bool | None) -> bool:
  """Resolve ``secure=None`` to the actual boolean for the current request."""
  if secure is not None:
    return secure
  try:
    from flask import request

    return request.is_secure
  except RuntimeError:
    return False
