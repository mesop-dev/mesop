import dataclasses
import json
import logging
from typing import Any

from mesop.runtime import runtime

logger = logging.getLogger(__name__)


def _resolve_secure(secure: bool | None) -> bool:
  """Resolve ``secure=None`` to the actual boolean for the current request.

  ``None`` auto-detects: returns ``True`` when the request is HTTPS,
  ``False`` when it is plain HTTP (e.g. local development).
  """
  if secure is not None:
    return secure
  try:
    from flask import request

    return request.is_secure
  except RuntimeError:
    # Flask raises RuntimeError when request is accessed outside an active
    # request context (e.g. unit tests). This should not occur in production
    # where event handlers always run inside a request context.
    logger.warning(
      "set_cookie: could not detect HTTPS (no active Flask request context);"
      " defaulting secure=False. This is expected in tests."
    )
    return False


def set_cookie(
  name_or_instance: "str | Any",
  value: str | None = None,
  *,
  max_age: int | None = None,
  path: str = "/",
  domain: str | None = None,
  secure: bool | None = None,
  httponly: bool = True,
  samesite: str = "Lax",
) -> None:
  """Set a browser cookie from within a Mesop event handler.

  !!! warning "Experimental"
      This API is experimental and may change in future releases.

  **Two call forms:**

  **Low-level** — supply the cookie name and raw string value yourself:

  .. code-block:: python

      me.set_cookie("session_id", "abc123", max_age=3600)

  Use this when you need full control over the cookie name and value format,
  or when you are *not* using ``@me.cookieclass``.

  **High-level** — pass a ``@me.cookieclass`` instance; the name is derived
  from the class and the value is JSON-serialised automatically:

  .. code-block:: python

      me.set_cookie(SessionCookie(username="alice"), max_age=3600)

  **When to use which form:**

  - Prefer the high-level form for structured data (auth sessions, user
    preferences, etc.).  It handles serialisation and, when the class is
    decorated with ``signed=True`` or ``encrypted=True``, security too.
  - Use the low-level form for opaque tokens or values managed by an
    external library.

  The cookie is applied via a lightweight follow-up POST request that the
  Mesop client makes to ``/__apply-cookies`` after receiving the server
  response.  This sidesteps the SSE/WebSocket streaming constraint that
  prevents setting ``Set-Cookie`` headers directly on the event-handler
  response.

  Args:
    name_or_instance: Either a ``str`` cookie name (low-level) or a
      ``@me.cookieclass`` instance (high-level).
    value: Raw string value — required when *name_or_instance* is a
      ``str``, ignored when it is a cookieclass instance.
    max_age: Lifetime in seconds.  ``None`` (default) creates a session
      cookie that expires when the browser closes.
    path: URL path scope for the cookie.  Defaults to ``"/"``.
    domain: Domain scope.  ``None`` (default) means the current domain.
    secure: When ``True``, the cookie is only sent over HTTPS.  When
      ``None`` (default), auto-detects from the request: ``True`` on
      HTTPS, ``False`` on plain HTTP.  Pass ``False`` explicitly to force
      HTTP-only (rarely needed).
    httponly: When ``True`` (default), JavaScript cannot access the cookie
      after it is stored in the browser, which mitigates XSS theft of
      session tokens.  Note that during the ``/__apply-cookies`` round-trip
      the cookie value is embedded in the signed ``ApplyCookiesCommand``
      token and briefly passes through browser JavaScript — so the value is
      not fully opaque to JS at write-time.  For values that must never be
      readable by JavaScript, store only an opaque server-side ID in the
      cookie and use ``@me.cookieclass(encrypted=True)`` to encrypt the
      token payload.
    samesite: ``"Lax"`` (default), ``"Strict"``, or ``"None"``.  Use
      ``"None"`` only together with ``secure=True``.
  """
  if isinstance(name_or_instance, str):
    # Low-level form: explicit name + raw string value.
    if value is None:
      raise TypeError(
        "set_cookie() requires a value when the first argument is a string.\n"
        "Example: me.set_cookie('session_id', 'abc123')\n"
        "To set a cookieclass cookie, pass an instance instead:\n"
        "  me.set_cookie(SessionCookie(username='alice'))"
      )
    runtime().context().set_cookie(
      name_or_instance,
      value,
      max_age=max_age,
      path=path,
      domain=domain,
      secure=_resolve_secure(secure),
      httponly=httponly,
      samesite=samesite,
    )
  else:
    # High-level form: cookieclass instance.
    from mesop.commands.cookie_class import (
      _COOKIE_CLASSES,
      _assert_is_cookieclass,
      _encode_value,
    )

    cls = type(name_or_instance)
    _assert_is_cookieclass(cls)
    meta = _COOKIE_CLASSES[cls]
    encoded = _encode_value(
      json.dumps(dataclasses.asdict(name_or_instance)), meta
    )
    runtime().context().set_cookie(
      meta.name,
      encoded,
      max_age=max_age,
      path=path,
      domain=domain,
      secure=_resolve_secure(secure),
      httponly=httponly,
      samesite=samesite,
    )


def delete_cookie(
  name: "str | type",
  *,
  path: str = "/",
  domain: str | None = None,
  secure: bool | None = None,
) -> None:
  """Delete a browser cookie from within a Mesop event handler.

  Instructs the browser to expire the cookie immediately by setting its
  ``Max-Age`` to ``0``.  The ``path`` and ``domain`` must match the values
  used when the cookie was originally set.

  *name* accepts either a plain string cookie name **or** a class decorated
  with ``@me.cookieclass``, in which case the cookie name is looked up
  automatically:

  .. code-block:: python

      me.delete_cookie("session_id")      # low-level: explicit name
      me.delete_cookie(SessionCookie)     # high-level: class lookup

  Args:
    name: Cookie name (``str``) or a ``@me.cookieclass``-decorated class.
    path: URL path scope that was used when creating the cookie.
    domain: Domain scope that was used when creating the cookie.
    secure: When ``True``, the deletion ``Set-Cookie`` header carries the
      ``Secure`` attribute.  When ``None`` (default), auto-detects from the
      current request — ``True`` on HTTPS, ``False`` on plain HTTP.  Pass
      ``False`` explicitly to force non-Secure (rarely needed).
  """
  resolved_secure = _resolve_secure(secure)
  if isinstance(name, str):
    runtime().context().delete_cookie(
      name, path=path, domain=domain, secure=resolved_secure
    )
  else:
    from mesop.commands.cookie_class import (
      _COOKIE_CLASSES,
      _assert_is_cookieclass,
    )

    _assert_is_cookieclass(name)
    runtime().context().delete_cookie(
      _COOKIE_CLASSES[name].name,
      path=path,
      domain=domain,
      secure=resolved_secure,
    )
