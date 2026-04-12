"""Example demonstrating me.set_cookie() and me.delete_cookie().

This example simulates a simple login/logout flow:
- On "Log in", a session cookie is set and the UI shows the logged-in state.
- On "Log out", the session cookie is deleted and the UI returns to the
  logged-out state.
- On page load the cookie is read from the request so the login state
  persists across hard refreshes and new tabs.
"""

import mesop as me
from flask import request


@me.stateclass
class State:
  logged_in: bool = False
  username: str = ""


def on_load(e: me.LoadEvent):
  state = me.state(State)
  session = request.cookies.get("demo_session", "")
  if session.startswith("user:"):
    state.logged_in = True
    state.username = session[len("user:"):]


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
      me.button("Log in as Alice", on_click=on_login, type="flat", color="primary")


def on_login(e: me.ClickEvent):
  state = me.state(State)
  state.logged_in = True
  state.username = "alice"
  me.set_cookie(
    "demo_session",
    "user:alice",
    # Short max_age so the demo cookie doesn't linger indefinitely.
    max_age=3600,
    httponly=True,
    # secure=False so the example works over plain HTTP in local dev.
    secure=False,
    samesite="Lax",
  )


def on_logout(e: me.ClickEvent):
  state = me.state(State)
  state.logged_in = False
  state.username = ""
  me.delete_cookie("demo_session")
