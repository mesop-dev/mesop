from mesop.runtime import runtime


def set_cookie(
  name: str,
  value: str,
  *,
  max_age: int | None = None,
  path: str = "/",
  domain: str | None = None,
  secure: bool = True,
  httponly: bool = True,
  samesite: str = "Lax",
) -> None:
  """
  Sets a browser cookie from within a Mesop event handler.

  The cookie is applied via a lightweight follow-up GET request that the
  Mesop client makes to ``/__apply-cookies`` after receiving the server
  response.  This sidesteps the SSE/WebSocket streaming constraint that
  prevents setting ``Set-Cookie`` headers directly on the event-handler
  response.

  Args:
    name: Cookie name.
    value: Cookie value.
    max_age: Lifetime in seconds.  ``None`` (default) creates a session
      cookie that expires when the browser closes.
    path: URL path scope for the cookie.  Defaults to ``"/"``.
    domain: Domain scope.  ``None`` (default) means the current domain.
    secure: When ``True`` (default), the cookie is only sent over HTTPS.
      Set to ``False`` for local HTTP development.
    httponly: When ``True`` (default), JavaScript cannot access the cookie,
      which mitigates XSS theft of session tokens.
    samesite: ``"Lax"`` (default), ``"Strict"``, or ``"None"``.  Use
      ``"None"`` only together with ``secure=True``.
  """
  runtime().context().set_cookie(
    name,
    value,
    max_age=max_age,
    path=path,
    domain=domain,
    secure=secure,
    httponly=httponly,
    samesite=samesite,
  )


def delete_cookie(
  name: "str | type",
  *,
  path: str = "/",
  domain: str | None = None,
) -> None:
  """
  Deletes a browser cookie from within a Mesop event handler.

  Instructs the browser to expire the named cookie immediately by setting
  its ``Max-Age`` to ``0``.  The ``path`` and ``domain`` must match the
  values used when the cookie was originally set.

  *name* can be either a plain string cookie name **or** a class decorated
  with ``@me.cookieclass``, in which case the cookie name is looked up
  automatically.

  Args:
    name: Cookie name (``str``) or a ``@me.cookieclass``-decorated class.
    path: URL path scope that was used when creating the cookie.
    domain: Domain scope that was used when creating the cookie.
  """
  if isinstance(name, str):
    runtime().context().delete_cookie(name, path=path, domain=domain)
  else:
    # Treat as a cookieclass type — look up its cookie name.
    from mesop.commands.cookie_class import (
      _COOKIE_CLASSES,
      _assert_is_cookieclass,
    )

    _assert_is_cookieclass(name)
    runtime().context().delete_cookie(
      _COOKIE_CLASSES[name], path=path, domain=domain
    )
