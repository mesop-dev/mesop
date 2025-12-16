"""
Simple test app to verify the fix for bug #1309:
me.navigate() in page load should work consistently.

To run this test:
1. Start the server: mesop test_navigate_on_load.py
2. Navigate to http://localhost:32123/
3. Verify that you are automatically redirected to /login
4. The page should show "Login Page" content
"""

import mesop as me


@me.stateclass
class State:
  authenticated: bool = False


def check_auth_on_load(e: me.LoadEvent):
  """On load handler that checks auth and redirects if needed."""
  state = me.state(State)
  if not state.authenticated:
    # This should now work consistently with the fix
    me.navigate('/login')


@me.page(path="/", on_load=check_auth_on_load)
def home():
  """Home page that should redirect to login if not authenticated."""
  me.text("Home Page - You should not see this if not authenticated")
  state = me.state(State)
  if state.authenticated:
    me.text("Welcome! You are authenticated.")
  else:
    me.text("ERROR: This should have redirected to /login")


@me.page(path="/login")
def login():
  """Login page."""
  me.text("Login Page", type="headline-4")
  me.text("This is the login page. The redirect worked!")

  def on_login(e: me.ClickEvent):
    state = me.state(State)
    state.authenticated = True
    me.navigate('/')

  me.button("Login", on_click=on_login)
