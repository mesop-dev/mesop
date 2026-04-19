# Auth

Mesop is designed to be auth provider agnostic. You can integrate any auth library you prefer, whether it's on the client-side (JavaScript) or server-side (Python). This guide covers several approaches so you can choose the one that fits your deployment.

| Approach | Best for |
|---|---|
| [Google Cloud IAP](#google-cloud-iap) | Apps already on App Engine or Cloud Run |
| [Firebase Authentication](#firebase-authentication) | Apps that need social sign-in or multi-provider auth |
| [Cookies](#cookies) | Persisting session tokens or structured data across requests; includes a [username/password login example](#username-and-password) (experimental) |
| [HTTP Basic Auth](#http-basic-auth) | Internal tools where a browser pop-up is acceptable and no login UI is needed |

> **Important:** Regardless of which approach you choose, always enforce authorization on the server side in your event handlers. Never rely solely on client-visible state to gate privileged actions. See the [state management security guide](./state-management.md#security-best-practices) for more details.

## Google Cloud IAP

[Google Cloud Identity-Aware Proxy (IAP)](https://cloud.google.com/iap) handles authentication entirely at the infrastructure level before any request reaches your Mesop app. This is the simplest approach if you are already deploying to App Engine or Cloud Run — there is no login UI to build and no tokens to manage in your app.

**How it works:**

1. You enable IAP on your App Engine or Cloud Run service in the Google Cloud Console.
2. Google handles the sign-in flow and only forwards authenticated requests to your app.
3. Each forwarded request includes a signed `X-Goog-IAP-JWT-Assertion` header containing the user's identity.
4. Your app verifies this header and trusts the identity inside it.

**Prerequisites:**

- A Google Cloud project with App Engine or Cloud Run
- IAP enabled on your service (see the [IAP docs](https://cloud.google.com/iap/docs/enabling-cloud-run) for setup)
- `google-auth` Python package (`pip install google-auth`)

**Finding your audience string:**

The audience value for JWT verification depends on your service type:

- **App Engine:** `/projects/PROJECT_NUMBER/apps/PROJECT_ID`
- **Cloud Run:** `/projects/PROJECT_NUMBER/global/backendServices/SERVICE_ID`

You can find `PROJECT_NUMBER` and `PROJECT_ID` in the Google Cloud Console. For Cloud Run, get `SERVICE_ID` from the [IAP settings page](https://cloud.google.com/iap/docs/signed-headers-howto#securing_iap_headers).

**Example:**

```python
# requirements.txt: google-auth

import os
import mesop as me
import google.auth.transport.requests
import google.oauth2.id_token
from flask import request

# Set via environment variable in production.
# Format for App Engine:  /projects/PROJECT_NUMBER/apps/PROJECT_ID
# Format for Cloud Run:   /projects/PROJECT_NUMBER/global/backendServices/SERVICE_ID
IAP_AUDIENCE = os.environ["IAP_AUDIENCE"]

_http_request = google.auth.transport.requests.Request()


def verify_iap_jwt(iap_jwt: str) -> dict:
    return google.oauth2.id_token.verify_token(
        iap_jwt,
        _http_request,
        audience=IAP_AUDIENCE,
        certs_url="https://www.gstatic.com/iap/verify/public_key",
    )


@me.stateclass
class State:
    user_email: str


def on_load(e: me.LoadEvent):
    iap_jwt = request.headers.get("X-Goog-IAP-JWT-Assertion")
    if not iap_jwt:
        # Header is absent — IAP is not in front of this request.
        # This can happen during local development. Gate accordingly.
        me.navigate("/unauthorized")
        return
    try:
        payload = verify_iap_jwt(iap_jwt)
    except Exception:
        me.navigate("/unauthorized")
        return
    me.state(State).user_email = payload["email"]


@me.page(path="/", on_load=on_load)
def page():
    state = me.state(State)
    me.text(f"Hello, {state.user_email}")


@me.page(path="/unauthorized")
def unauthorized_page():
    me.text("Access denied.")
```

**Local development tip:** The IAP header is absent when running locally. You can detect this and either skip the check (during development only) or inject a fake header via a local reverse proxy like [Cloud Run proxy](https://cloud.google.com/run/docs/testing/local).

## Firebase Authentication

This guide will walk you through the process of integrating Firebase Authentication with Mesop using a custom web component.

**Pre-requisites:** You will need to create a [Firebase](https://firebase.google.com/) account and project. It's free to get started with Firebase and use Firebase auth for small projects, but refer to the [pricing page](https://firebase.google.com/pricing) for the most up-to-date information.

We will be using three libraries from Firebase to build an end-to-end auth flow:

- [Firebase Web SDK](https://firebase.google.com/docs/web/learn-more): Allows you to call Firebase services from your client-side JavaScript code.
- [FirebaseUI Web](https://github.com/firebase/firebaseui-web): Provides a simple, customizable auth UI integrated with the Firebase Web SDK.
- [Firebase Admin SDK (Python)](https://firebase.google.com/docs/auth/admin/verify-id-tokens#verify_id_tokens_using_the_firebase_admin_sdk): Provides server-side libraries to integrate Firebase services, including Authentication, into your Python applications.

Let's dive into how we will use each one in our Mesop app.

### Web component

The Firebase Authentication web component is a custom component built for handling the user authentication process. It's implemented using [Lit](https://lit.dev/), a simple library for building lightweight web components.

#### JS code

```javascript title="firebase_auth_component.js"
--8<-- "mesop/examples/web_component/firebase_auth/firebase_auth_component.js"
```

**What you need to do:**

- Replace `firebaseConfig` with your Firebase project's config. Read the [Firebase docs](https://firebase.google.com/docs/web/learn-more#config-object) to learn how to get yours.
- Replace the URLs `signInSuccessUrl` with your Mesop page path and `tosUrl` and `privacyPolicyUrl` to your terms and services and privacy policy page respectively.

**How it works:**

- This creates a simple and configurable auth UI using FirebaseUI Web.
- Once the user has signed in, then a sign out button is shown.
- Whenever the user signs in or out, the web component dispatches an event to the Mesop server with the auth token, or absence of it.
- See our [web component docs](../web-components/quickstart.md#javascript-module) for more details.

#### Python code

```python title="firebase_auth_component.py"
--8<-- "mesop/examples/web_component/firebase_auth/firebase_auth_component.py"
```

**How it works:**

- Implements the Python side of the Mesop web component. See our [web component docs](../web-components/quickstart.md#python-module) for more details.

### Integrating into the app

Let's put it all together:

```python title="firebase_auth_app.py"
--8<-- "mesop/examples/web_component/firebase_auth/firebase_auth_app.py"
```

*Note* You must add `firebase-admin` to your Mesop app's `requirements.txt` file

**How it works:**

- The `firebase_auth_app.py` module integrates the Firebase Auth web component into the Mesop app. It initializes the Firebase app, defines the page where the Firebase Auth web component will be used, and sets up the state to store the user's email.
- The `on_auth_changed` function is triggered whenever the user's authentication state changes. If the user is signed in, it verifies the user's ID token and stores the user's email in the state. If the user is not signed in, it clears the email from the state.

### Next steps

Congrats! You've now built an authenticated app with Mesop from start to finish. Read the [Firebase Auth docs](https://firebase.google.com/docs/auth) to learn how to configure additional sign-in options and much more.

## Cookies

!!! warning "Experimental"
    The cookie API is experimental. The interface may change in future releases.

Mesop provides a first-class cookie API so you can persist small pieces of data (session tokens, user preferences, etc.) in the browser without managing raw `Set-Cookie` headers yourself.

!!! note "MESOP_COOKIE_SECRET_KEY required"
    Set [`MESOP_COOKIE_SECRET_KEY`](../api/config.md#mesop_cookie_secret_key) before starting Mesop:

    ```sh
    MESOP_COOKIE_SECRET_KEY=your-random-secret mesop main.py
    ```

    Generate a strong key:

    ```sh
    python -c "import secrets; print(secrets.token_hex(32))"
    ```

### How it works

Mesop event handlers run inside a streaming response (SSE or WebSockets). HTTP response headers — including `Set-Cookie` — are committed to the client *before* the event-handler body executes, so cookies cannot be set directly on the handler response. Instead, cookies are applied via a lightweight two-step protocol:

1. Your event handler calls `me.set_cookie()`.
2. Mesop encodes the pending cookie operations into a short-lived itsdangerous-signed token and sends an `ApplyCookiesCommand` to the browser.  Any server worker that holds the same [`MESOP_COOKIE_SECRET_KEY`](../api/config.md#mesop_cookie_secret_key) can verify and redeem the token.
3. The Mesop client POSTs the token to `/__apply-cookies`, which verifies the signature, marks the token's nonce as used (single-use within a process), and responds with the `Set-Cookie` headers.

This is transparent to your application code.

### `@me.cookieclass` — structured cookies

The recommended API is `@me.cookieclass`, which works like `@me.stateclass` but for cookies.  Fields are JSON-serialised automatically.

```python
import mesop as me

@me.cookieclass
class SessionCookie:
    username: str = ""
    role: str = "guest"
```

#### Reading a cookie

Call `me.cookie(SessionCookie)` inside `on_load` or any event handler.  If the cookie is absent or unparseable, a fresh default instance is returned — no exception is raised.

```python
def on_load(e: me.LoadEvent):
    session = me.cookie(SessionCookie)
    if session.username:
        state = me.state(State)
        state.logged_in = True
        state.username = session.username
```

#### Writing / updating a cookie

Pass a cookieclass instance to `me.set_cookie()`.  The cookie name is derived from the class, and the fields are JSON-serialised automatically.

```python
def on_login(e: me.ClickEvent):
    me.set_cookie(
        SessionCookie(username="alice", role="admin"),
        max_age=3600,   # seconds; omit for a session cookie
    )
```

When `secure` is omitted it auto-detects HTTPS — so the same code works in local HTTP development and in production HTTPS deployments without any extra configuration.

#### Deleting a cookie

```python
def on_logout(e: me.ClickEvent):
    me.delete_cookie(SessionCookie)   # pass the class, not a string
```

### Signed and encrypted cookies

By default `@me.cookieclass` stores the JSON value in plain text — readable in browser DevTools.  For cookies that carry sensitive data you can add tamper-protection or full encryption by setting `signed=True` or `encrypted=True` on the decorator.

| Option | Protection | Contents visible? | Extra dependency |
|---|---|---|---|
| *(default)* | None | Yes (plain JSON) | — |
| `signed=True` | HMAC — tampering detected on read | Yes (Base64) | — |
| `encrypted=True` | Fernet — contents hidden | No | `pip install cryptography` |

```python
# Tamper-proof — contents still visible in DevTools, but any modification
# is detected and the cookie is silently discarded on the next read.
@me.cookieclass(signed=True)
class SessionCookie:
    username: str = ""

# Fully encrypted — contents hidden; requires pip install cryptography.
@me.cookieclass(encrypted=True)
class SessionCookie:
    username: str = ""
```

The read (`me.cookie()`) and write (`me.set_cookie()`) calls are identical regardless of the protection level — the signing or encryption is applied transparently.

### Low-level API

If you need full control over the cookie name and value format — for example when storing an opaque session token generated by an external library — use `me.set_cookie()` with explicit string arguments.

> **When to use which form:** prefer the cookieclass form for structured data.  Use the low-level form only for raw opaque values.

#### `me.cookie()`

```python
token = me.cookie("session_id")         # low-level: raw string value (or "" if absent)
session = me.cookie(SessionCookie)      # high-level: typed cookieclass instance
```

#### `me.set_cookie()`

```python
# Low-level: explicit name + raw string value.
me.set_cookie(
    "session_id",
    "abc123",
    max_age=3600,        # None → session cookie
    path="/",
    domain=None,         # None → current domain
    secure=None,         # None → auto-detect HTTPS (recommended default)
    httponly=True,       # hidden from JavaScript
    samesite="Lax",      # "Lax" | "Strict" | "None"
)

# High-level: cookieclass instance — name and serialisation handled automatically.
me.set_cookie(SessionCookie(username="alice"), max_age=3600)
```

#### `me.delete_cookie()`

```python
me.delete_cookie("session_id")      # low-level: explicit string name
me.delete_cookie(SessionCookie)     # high-level: class lookup
```

### Username and Password

This example combines a username/password login form with cookie-backed sessions. After a successful login the verified username is written to a signed cookie, so the session persists across page refreshes and new tabs — unlike a state-only approach, which is cleared on any hard navigation.

> **Warning:** Rolling your own auth is error-prone. For production apps with many users, prefer a managed solution like [Google Cloud IAP](#google-cloud-iap) or [Firebase Authentication](#firebase-authentication).

**Prerequisites:**

- `werkzeug` (already installed with Mesop — used for password hashing)

**Step 1 — Store hashed passwords**

Never store plaintext passwords. Use `werkzeug.security` to hash them at setup time and store only the hash.

```python
from werkzeug.security import generate_password_hash

# Run this once to generate the hash, then store it securely.
print(generate_password_hash("my-secret-password"))
```

**Step 2 — Full example**

```python
# cookie_auth_app.py
# Run: gunicorn --bind 0.0.0.0:8080 cookie_auth_app:me
#
# One-time setup:
#   export ALICE_PASSWORD_HASH="$(python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('hunter2'))")"
#
# Login with: username "alice", password "hunter2"

import os
import mesop as me
from werkzeug.security import check_password_hash

# In production, load from a database.
USERS: dict[str, str] = {
    "alice": os.environ["ALICE_PASSWORD_HASH"],
}

@me.cookieclass(signed=True)
class SessionCookie:
    username: str = ""

@me.stateclass
class State:
    username: str = ""
    username_input: str = ""
    password_input: str = ""
    error: str = ""

def on_load(e: me.LoadEvent):
    session = me.cookie(SessionCookie)
    if session.username:
        me.state(State).username = session.username

def on_username_input(e: me.InputEvent):
    me.state(State).username_input = e.value

def on_password_input(e: me.InputEvent):
    me.state(State).password_input = e.value

def on_login(e: me.ClickEvent):
    state = me.state(State)
    username = state.username_input.strip()

    if not username or not state.password_input:
        state.error = "Please enter a username and password."
        return

    stored_hash = USERS.get(username)
    if not stored_hash or not check_password_hash(stored_hash, state.password_input):
        state.error = "Invalid username or password."
        state.password_input = ""
        return

    state.username = username
    state.password_input = ""
    state.error = ""
    me.set_cookie(SessionCookie(username=username), max_age=86400)  # 1 day

def on_logout(e: me.ClickEvent):
    state = me.state(State)
    state.username = ""
    me.delete_cookie(SessionCookie)

@me.page(path="/", on_load=on_load)
def main():
    state = me.state(State)

    if not state.username:
        with me.box(style=me.Style(padding=me.Padding.all(32), max_width=320)):
            me.text("Sign in", type="headline-5")
            if state.error:
                me.text(state.error, style=me.Style(color="red"))
            me.input(label="Username", on_input=on_username_input)
            me.input(label="Password", type="password", on_input=on_password_input)
            me.button("Sign in", on_click=on_login, type="flat")
    else:
        with me.box(style=me.Style(padding=me.Padding.all(32))):
            me.text(f"Welcome, {state.username}!")
            me.button("Sign out", on_click=on_logout, type="flat")
```

**Multiple protected pages**

For apps with several protected pages, add `on_load=on_load` to each page and check `state.username` at the top:

```python
def _require_login() -> bool:
    state = me.state(State)
    if not state.username:
        _render_login_form()
        return False
    return True

@me.page(path="/dashboard", on_load=on_load)
def dashboard():
    if not _require_login():
        return
    # Protected dashboard content...

@me.page(path="/settings", on_load=on_load)
def settings():
    if not _require_login():
        return
    # Protected settings content...
```

**Security checklist:**

- Never store plaintext passwords — use `generate_password_hash` / `check_password_hash`.
- Never store password hashes in source code or committed files — use a secret manager (e.g. [GCP Secret Manager](https://cloud.google.com/secret-manager), [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)) or a `.env` file listed in `.gitignore` for local development.
- Use `@me.cookieclass(signed=True)` (or `encrypted=True`) to prevent cookie tampering or content inspection.
- Validate and sanitize all user inputs (see the [state management guide](./state-management.md#validate-input-before-updating-state)).
- For genuine access control, use [Google Cloud IAP](#google-cloud-iap) or [Firebase Authentication](#firebase-authentication).

### Security notes

- **`httponly=True` (default):** The cookie is not accessible to JavaScript, which mitigates XSS-based session theft.  It is still visible in browser DevTools.
- **`secure=None` (default):** Auto-detects HTTPS — `True` in production, `False` on local HTTP.  Pass `secure=True` to enforce HTTPS-only regardless of environment.
- **`samesite="Lax"` (default):** Protects against most CSRF attacks.  Use `"Strict"` for additional protection at the cost of some UX friction on cross-site navigations.
- **Cookie value size:** Browsers limit individual cookies to ~4 KB.  Use server-side session storage (database, Redis, etc.) for larger payloads and store only an opaque session ID in the cookie.
- **Sensitive data:** Use `@me.cookieclass(encrypted=True)` to hide cookie contents, or store only an opaque token and keep sensitive data server-side.
- **Cookie value visibility during apply:** When `me.set_cookie()` is called, the pending cookie values are embedded in the `ApplyCookiesCommand` token that passes through browser JavaScript before being POSTed to `/__apply-cookies`.  The token is HMAC-signed but not encrypted, so the values are Base64-readable in that brief window.  For cookies that must never be visible to JavaScript (e.g. an `httponly` session token whose raw value is sensitive), use `@me.cookieclass(encrypted=True)` — the value is Fernet-encrypted before it ever leaves the server, so the token carries only ciphertext.

---

## HTTP Basic Auth

HTTP Basic Auth lets the browser display a native username/password pop-up with no login page required. It is a good fit for internal tools where:

- The entire app should be protected (no public pages)
- You want the simplest possible setup with zero UI code
- The app is served over HTTPS (required — Basic Auth sends credentials in plaintext otherwise)

> **Warning:** Do not use HTTP Basic Auth over plain HTTP. Always deploy behind HTTPS.

**How it works:**

A WSGI middleware wrapper intercepts every request before it reaches Mesop. If the `Authorization` header is missing or the credentials are wrong, the middleware returns a `401` response immediately and the browser shows its built-in sign-in dialog. Valid requests are passed through to Mesop as normal.

**Prerequisites:**

- `werkzeug` (already installed with Mesop)

**Example:**

```python
import base64
import os
import mesop as me
from werkzeug.security import check_password_hash, generate_password_hash
from mesop import create_wsgi_app

# In production, load from environment variables or a database.
# Generate hashes with: werkzeug.security.generate_password_hash("my-password")
USERS: dict[str, str] = {
    "alice": os.environ["ALICE_PASSWORD_HASH"],
}

REALM = "My Internal Tool"


class BasicAuthMiddleware:
    """WSGI middleware that enforces HTTP Basic Auth on every request."""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # Parse the Authorization header.
        auth_header = environ.get("HTTP_AUTHORIZATION", "")
        username = self._check_credentials(auth_header)

        if username is None:
            # Credentials missing or wrong — ask the browser to prompt.
            start_response(
                "401 Unauthorized",
                [
                    ("Content-Type", "text/plain"),
                    ("WWW-Authenticate", f'Basic realm="{REALM}"'),
                ],
            )
            return [b"Unauthorized"]

        # Pass the verified username to the app via an environment variable
        # so Mesop handlers can read it with os.environ or flask.request.environ.
        environ["basic_auth_user"] = username
        return self.app(environ, start_response)

    def _check_credentials(self, auth_header: str) -> str | None:
        """Return the username if credentials are valid, otherwise None."""
        if not auth_header.startswith("Basic "):
            return None
        try:
            decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
            username, _, password = decoded.partition(":")
        except Exception:
            return None

        stored_hash = USERS.get(username)
        if stored_hash and check_password_hash(stored_hash, password):
            return username
        return None


# ------------------------------------------------------------------ #
# Mesop app
# ------------------------------------------------------------------ #

@me.stateclass
class State:
    username: str


def on_load(e: me.LoadEvent):
    from flask import request
    # Read the username set by the middleware.
    me.state(State).username = request.environ.get("basic_auth_user", "")


@me.page(path="/", on_load=on_load)
def page():
    me.text(f"Hello, {me.state(State).username}!")


# Wrap the Mesop WSGI app with the Basic Auth middleware.
app = BasicAuthMiddleware(create_wsgi_app(debug_mode=False))
```

Run with Gunicorn:

```
gunicorn --bind 0.0.0.0:8080 'your_module:app'
```

**Security checklist:**

- Only use HTTP Basic Auth behind HTTPS — credentials are only Base64-encoded, not encrypted.
- Store only hashed passwords, never plaintext.
- Never put credentials in source code or committed files. Use your platform's secret management solution — for example [GCP Secret Manager](https://cloud.google.com/secret-manager), [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/), or a `.env` file that is listed in `.gitignore` for local development.
- Consider combining with an IP allowlist at the network/load-balancer level for extra protection.
