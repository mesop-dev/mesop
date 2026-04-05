# Auth

Mesop is designed to be auth provider agnostic. You can integrate any auth library you prefer, whether it's on the client-side (JavaScript) or server-side (Python). This guide covers several approaches so you can choose the one that fits your deployment.

| Approach | Best for |
|---|---|
| [Google Cloud IAP](#google-cloud-iap) | Apps already on App Engine or Cloud Run |
| [Firebase Authentication](#firebase-authentication) | Apps that need social sign-in or multi-provider auth |
| [Username & Password](#username-and-password) | Simple internal tools or apps with a mix of public and private pages |
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

## Username and Password

This approach is suitable for internal tools, prototypes, or apps that have a mix of public and private pages and do not need social sign-in. It does not require any external service.

> **Warning:** Rolling your own auth is error-prone. For production apps with many users, prefer a managed solution like [Google Cloud IAP](#google-cloud-iap) or [Firebase Authentication](#firebase-authentication). If you do use this approach, make sure you understand the security considerations below.

**How it works:**

1. A `/login` page collects a username and password.
2. The event handler verifies the password against a stored hash.
3. On success, a signed, `HttpOnly` session cookie is set so authentication persists across page refreshes.
4. Protected pages read and verify the cookie in their `on_load` handler.

**Prerequisites:**

- `werkzeug` (already installed with Mesop — used for password hashing)
- `itsdangerous` (already installed with Mesop — used for signing the session cookie)

**Step 1 — Store hashed passwords**

Never store plaintext passwords. Use `werkzeug.security` to hash them at setup time and store only the hash.

```python
from werkzeug.security import generate_password_hash

# Run this once to generate the hash, then store it (e.g. in a database or env var).
print(generate_password_hash("my-secret-password"))
```

**Step 2 — Full example**

```python
# requirements: mesop (werkzeug and itsdangerous are included)

import os
import mesop as me
from flask import request, after_this_request
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.security import check_password_hash

# ------------------------------------------------------------------ #
# Configuration
# ------------------------------------------------------------------ #

# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
# Store in an environment variable, never in source code.
SECRET_KEY = os.environ["SESSION_SECRET_KEY"]

# Session cookie expires after 8 hours.
SESSION_MAX_AGE_SECONDS = 8 * 60 * 60

_signer = URLSafeTimedSerializer(SECRET_KEY)

# In production, load credentials from a database.
# Hashes were generated with werkzeug.security.generate_password_hash().
USERS: dict[str, str] = {
    "alice": os.environ["ALICE_PASSWORD_HASH"],
}

# ------------------------------------------------------------------ #
# Session helpers
# ------------------------------------------------------------------ #

def _create_session_cookie(username: str) -> str:
    return _signer.dumps(username)


def _verify_session_cookie(cookie: str) -> str | None:
    """Return the username if the cookie is valid, otherwise None."""
    try:
        return _signer.loads(cookie, max_age=SESSION_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None


def _get_authenticated_user() -> str | None:
    """Read and verify the session cookie from the current request."""
    cookie = request.cookies.get("session")
    if not cookie:
        return None
    return _verify_session_cookie(cookie)

# ------------------------------------------------------------------ #
# State
# ------------------------------------------------------------------ #

@me.stateclass
class LoginState:
    username_input: str
    password_input: str
    error: str


@me.stateclass
class AppState:
    username: str

# ------------------------------------------------------------------ #
# Login page
# ------------------------------------------------------------------ #

def on_username_input(e: me.InputEvent):
    me.state(LoginState).username_input = e.value


def on_password_input(e: me.InputEvent):
    me.state(LoginState).password_input = e.value


def on_login(e: me.ClickEvent):
    state = me.state(LoginState)

    # Basic input validation.
    username = state.username_input.strip()
    if not username or not state.password_input:
        state.error = "Please enter a username and password."
        return

    # Verify credentials.
    stored_hash = USERS.get(username)
    if not stored_hash or not check_password_hash(stored_hash, state.password_input):
        state.error = "Invalid username or password."
        return

    # Set a signed, HttpOnly cookie so the session persists across refreshes.
    token = _create_session_cookie(username)

    @after_this_request
    def set_cookie(response):
        response.set_cookie(
            "session",
            token,
            max_age=SESSION_MAX_AGE_SECONDS,
            httponly=True,   # Not accessible from JavaScript.
            secure=True,     # Only sent over HTTPS. Set to False for local dev.
            samesite="Lax",
        )
        return response

    me.navigate("/app")


@me.page(path="/login")
def login_page():
    state = me.state(LoginState)
    with me.box(style=me.Style(padding=me.Padding.all(24), max_width=320)):
        me.text("Sign in", type="headline-5")
        if state.error:
            me.text(state.error, style=me.Style(color="red"))
        me.input(label="Username", on_input=on_username_input)
        me.input(label="Password", type="password", on_input=on_password_input)
        me.button("Sign in", on_click=on_login, type="flat")

# ------------------------------------------------------------------ #
# Protected page
# ------------------------------------------------------------------ #

def on_app_load(e: me.LoadEvent):
    username = _get_authenticated_user()
    if not username:
        me.navigate("/login")
        return
    me.state(AppState).username = username


@me.page(path="/app", on_load=on_app_load)
def app_page():
    state = me.state(AppState)
    me.text(f"Welcome, {state.username}!")
    # ... rest of the page
```

**Security checklist:**

- Always set `httponly=True` on the session cookie so JavaScript cannot read it.
- Always set `secure=True` in production so the cookie is only sent over HTTPS.
- Never store plaintext passwords — use `generate_password_hash` / `check_password_hash`.
- Never store `SECRET_KEY` or password hashes in source code or committed files — use a secret manager (e.g. [GCP Secret Manager](https://cloud.google.com/secret-manager), [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)) or a `.env` file listed in `.gitignore` for local development.
- Re-verify the session cookie on every protected `on_load`, not just once at login.
- Validate and sanitize all user inputs before using them (see the [state management guide](./state-management.md#validate-input-before-updating-state)).

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
