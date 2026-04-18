"""Example demonstrating @me.cookieclass, me.cookie(), me.set_cookie(),
and me.delete_cookie().

This example simulates a simple login/logout flow using the structured
cookieclass API:
- @me.cookieclass turns a plain dataclass into a cookie-backed store whose
  fields are JSON-serialised automatically.
- me.cookie(SessionCookie) reads the cookie from the current request and
  returns a populated instance (or a default instance if the cookie is absent).
- me.set_cookie(instance) serialises the instance and schedules the browser
  to set the cookie via the /__apply-cookies endpoint.
- me.delete_cookie(SessionCookie) removes the cookie by class.

The login state persists across hard refreshes and new tabs because the
cookie is read in on_load.

Start Mesop with:
  MESOP_COOKIE_SECRET_KEY=<your-secret> mesop main.py
"""

import dataclasses

import mesop as me


@me.cookieclass
@dataclasses.dataclass
class SessionCookie:
  username: str = ""


@me.stateclass
class State:
  logged_in: bool = False
  username: str = ""


def on_load(e: me.LoadEvent):
  session = me.cookie(SessionCookie)
  if session.username:
    state = me.state(State)
    state.logged_in = True
    state.username = session.username


@me.page(path="/set_cookie", on_load=on_load)
def page():
  state = me.state(State)
  with me.box(style=me.Style(padding=me.Padding.all(24), max_width=400)):
    me.text("Cookie example", type="headline-5")
    if state.logged_in:
      me.text(f"Logged in as: {state.username}")
      me.button("Log out", on_click=on_logout, type="flat", color="warn")
    else:
      me.text("Not logged in.")
      me.button(
        "Log in as Alice", on_click=on_login, type="flat", color="primary"
      )


def on_login(e: me.ClickEvent):
  state = me.state(State)
  state.logged_in = True
  state.username = "alice"
  # secure=None (default) auto-detects HTTPS vs HTTP so this works in both
  # local dev (HTTP) and production (HTTPS) without any extra config.
  me.set_cookie(SessionCookie(username="alice"), max_age=3600)


def on_logout(e: me.ClickEvent):
  state = me.state(State)
  state.logged_in = False
  state.username = ""
  me.delete_cookie(SessionCookie)
