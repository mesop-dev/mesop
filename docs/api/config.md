# Config

## Overview

Mesop is configured at the application level using environment variables.

## Configuration values

### MESOP_STATIC_FOLDER

> **NOTE:** This feature will be enabled by default in the next Mesop release and set to use `static` as the default static folder. You can still set it to another directory or `""` to disable the feature.

Allows access to static files from the Mesop server.

It is important to know that the specified folder path is relative to the current
working directory where the Mesop command is run. Absolute paths are not allowed.

Example:

In this case, the current working directory is `/srv`, which means Mesop will make
`/srv/static` the static folder.

```bash
cd /srv
MESOP_STATIC_FOLDER=static mesop app/main.py
```

Here are some examples of valid paths. Let's assume the current working directory is
`/srv/`

- `static` becomes `/srv/static`
- `static/` becomes `/srv/static`
- `static/assets` becomes `/srv/static/assets`
- `./static` becomes `/srv/static`
- `./static/` becomes `/srv/static`
- `./static/assets` becomes `/srv/static/assets`

Invalid paths will raise `MesopDeveloperException`. Here are some examples:

- Absolute paths (e.g. `/absolute/path`)
- `.`
- `./`
- `..`
- `../`

### MESOP_STATIC_URL_PATH

This is the base URL path from which files for your specified static folder will be
made viewable.

The static URL path is only recognized if `MESOP_STATIC_FOLDER` is set.

For example, given `MESOP_STATIC_FOLDER=static` and `MESOP_STATIC_URL_PATH=/assets`, the
file `static/js/script.js` can be viewable from the URL path `/assets/js/script.js`.

**Default:** `/static`

### MESOP_STATE_SESSION_BACKEND

Sets the backend to use for caching state data server-side. This makes it so state does
not have to be sent to the server on every request, reducing bandwidth, especially if
you have large state objects.

The backend options available at the moment are `memory`, `file`, `sql`, and `firestore`.

#### memory

Users should be careful when using the `memory` backend. Each Mesop process has their
own RAM, which means cache misses will be common if each server has multiple processes
and there is no session affinity. In addition, the amount of RAM must be carefully
specified per instance in accordance with the expected user traffic and state size.

The safest option for using the `memory` backend is to use a single process with a
good amount of RAM. Python is not the most memory efficient, especially when saving data
structures such as dicts.

The drawback of being limited to a single process is that requests will take longer to
process since only one request can be handled at a time. This is especially problematic
if your application contains long running API calls.

If session affinity is available, you can scale up multiple instances, each running
single processes.

#### file

Users should be careful when using the `file` backend. Each Mesop instance has their
own disk, which can be shared among multiple processes. This means cache misses will be
common if there are multiple instances and no session affinity.

If session affinity is available, you can scale up multiple instances, each running
multiple Mesop processes. If no session affinity is available, then you can only
vertically scale a single instance.

The bottleneck with this backend is the disk read/write performance. The amount of disk
space must also be carefully specified per instance in accordance with the expected user
traffic and state size.

You will also need to specify a directory to write the state data using
`MESOP_STATE_SESSION_BACKEND_FILE_BASE_DIR`.

#### SQL

> NOTE: Setting up and configuring databases is out of scope of this document.

This option uses [SqlAlchemy](https://www.sqlalchemy.org/) to store Mesop state sessions
in supported SQL databases, such as SQLite3 and PostgreSQL. You can also connect to
hosted options, such as GCP CloudSQL.

If you use SQLite3, you cannot use an in-memory database. It has to be a file. This
option has similar pros/cons as the `file` backend. Mesop uses the default configuration
for SQLite3, so the performance will not be optimized for Mesop's usage patterns.
SQLite3 is OK for development purposes.

Using a database like PostgreSQL will allow for better scalability, both vertically and
horizontally, since the database is decoupled from the Mesop server.

The drawback here is that this requires knowledge of the database you're using. At
minimum, you will need to create a database and a database user with the right
privileges. You will also need to create the database table, which you can create
with this script. You will need to update the CONNECTION_URI and TABLE_NAME to match
your database and settings. Also the database user for this script will need privileges
to create tables on the target database.

```python
from sqlalchemy import (
  Column,
  DateTime,
  LargeBinary,
  MetaData,
  String,
  Table,
  create_engine,
)

CONNECTION_URI = "your-database-connection-uri"
# Update to "your-table-name" if you've overridden `MESOP_STATE_SESSION_BACKEND_SQL_TABLE`.
TABLE_NAME = "mesop_state_session"

db = create_engine(CONNECTION_URI)
metadata = MetaData()
table = Table(
  TABLE_NAME,
  metadata,
  Column("token", String(23), primary_key=True),
  Column("states", LargeBinary, nullable=False),
  Column("created_at", DateTime, nullable=False, index=True),
)

metadata.create_all(db)
```

The Mesop server will raise a `sqlalchemy.exc.ProgrammingError` if there is a
database configuration issue.

By default, Mesop will use the table name `mesop_state_session`, but this can be
overridden using `MESOP_STATE_SESSION_BACKEND_SQL_TABLE`.

#### GCP Firestore

This options uses [GCP Firestore](https://cloud.google.com/firestore?hl=en) to store
Mesop state sessions. The `(default)` database has a free tier that can be used for
for small demo applications with low traffic and moderate amounts of state data.

Since Firestore is decoupled from your Mesop server, it allows you to scale vertically
and horizontally without the considerations you'd need to make for the `memory` and
`file` backends.

In order to use Firestore, you will need a Google Cloud account with Firestore enabled.
Follow the instructions for [creating a Firestore in Native mode database](https://cloud.google.com/firestore/docs/create-database-server-client-library#create_a_in_native_mode_database).

Mesop is configured to use the `(default)` Firestore only. The GCP project is determined
using the Application Default Credentials (ADC) which is automatically configured for
you on GCP services, such as Cloud Run.

For local development, you can run this command:

```sh
gcloud auth application-default login
```

If you have multiple GCP projects, you may need to update the project associated
with the ADC:

```sh
GCP_PROJECT=gcp-project
gcloud config set project $GCP_PROJECT
gcloud auth application-default set-quota-project $GCP_PROJECT
```

Mesop leverages Firestore's [TTL policies](https://firebase.google.com/docs/firestore/ttl)
to delete stale state sessions. This needs to be set up using the following command,
otherwise old data will accumulate unnecessarily.

```sh
COLLECTION_NAME=collection_name
gcloud firestore fields ttls update expiresAt \
  --collection-group=$COLLECTION_NAME
```

By default, Mesop will use the collection name `mesop_state_sessions`, but this can be
overridden using `MESOP_STATE_SESSION_BACKEND_FIRESTORE_COLLECTION`.

**Default:** `none`

### MESOP_STATE_SESSION_BACKEND_FILE_BASE_DIR

This is only used when the `MESOP_STATE_SESSION_BACKEND` is set to `file`. This
parameter specifies where Mesop will read/write the session state. This means the
directory must be readable and writeable by the Mesop server processes.

### MESOP_STATE_SESSION_BACKEND_FIRESTORE_COLLECTION

This is only used when the `MESOP_STATE_SESSION_BACKEND` is set to `firestore`. This
parameter specifies which Firestore collection that Mesop will write state sessions to.

**Default:** `mesop_state_sessions`

### MESOP_STATE_SESSION_BACKEND_SQL_CONNECTION_URI

This is only used when the `MESOP_STATE_SESSION_BACKEND` is set to `sql`. This
parameter specifies the database connection string. See the [SqlAlchemy docs for more details](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls).

**Default:** `mesop_state_session`

### MESOP_STATE_SESSION_BACKEND_SQL_TABLE

This is only used when the `MESOP_STATE_SESSION_BACKEND` is set to `sql`. This
parameter specifies which SQL database table that Mesop will write state sessions to.

**Default:** `mesop_state_session`

### MESOP_PROD_UNREDACTED_ERRORS

Mesop, by default, only shows unredacted errors in debug mode.

If you run in prod mode, the errors are redacted (internal errors are given a generic message "Sorry, there was an error. Please contact the developer.") and the tracebacks are not shown.

If you want to show unredacted errors, including in prod mode, set this to `true`. This may be useful if you're deploying a Mesop app internally and want to get error details even in production.

## Experimental configuration values

These configuration values are experimental and are subject to breaking change, including removal in future releases.

### MESOP_CONCURRENT_UPDATES_ENABLED (DEPRECATED)

!!! danger "Deprecated experimental feature"

      This experimental feature has been removed in Mesop v1. Use `MESOP_WEBSOCKETS_ENABLED` instead.

Allows concurrent updates to state in the same session. If this is not updated, then updates are queued and processed sequentially.

By default, this is not enabled. You can enable this by setting it to `true`.

### MESOP_WEBSOCKETS_ENABLED

!!! warning "Experimental feature"

    This is an experimental feature and is subject to breaking change. Please follow [https://github.com/mesop-dev/mesop/issues/1028](https://github.com/mesop-dev/mesop/issues/1028) for updates.

This uses WebSockets instead of HTTP Server-Sent Events (SSE) as the transport protocol for UI updates. Using WebSockets also changes the Mesop server architecture to be stateful (e.g. meaning a server restart or routing to a different server instance means the user will lose state). If you enable this feature, then you should ensure the following:

- Either a single server instance is used *or* you route a particular user to the same server for a given session (i.e. [session affinity](https://cloud.google.com/run/docs/configuring/session-affinity)).
- Either ensure user state is *not* critical (e.g. it's OK if it's cleared out due to server restart, which could happen at any time on typical cloud infrastructure) or is persisted somewhere (e.g. written to a database).

Enabling this also allows user events to be handled concurrently, which is particularly useful supporting interactivity for long-running event handlers.

By default, this is not enabled. You can enable this by setting it to `true`.

### MESOP_APP_BASE_PATH

This is the base path used to resolve other paths, particularly for serving static files. Must be an absolute path. This is rarely needed because the default of using the current working directory is usually sufficient.

### MESOP_BASE_URL_PATH

Base URL path for serving the Mesop application. Set this if your app is served from a non-root path (e.g. `/myapp`). All HTTP routes, static assets, and API calls will be prefixed with this path. The value must start with a slash but should not include a trailing slash.

### MESOP_HTTP_CACHE_JS_BUNDLE

Enables HTTP caching for the main JS bundle (i.e. prod_bundle.js) served by Mesop. This minimizes unnecessary HTTP requests for the JS bundle.

Note: this does *not* cache other JS files like web components, which are configured separately (see below).

### MESOP_WEB_COMPONENTS_HTTP_CACHE_KEY

Enables HTTP caching for the web component entry point modules.

Note: this does *not* cache JS files imported by the web component entry modules.

### MESOP_COOKIE_SECRET_KEY

!!! warning "Experimental"
    The signed/encrypted cookie API is experimental and may change in future releases.

Secret key required for using Mesop cookies.

- **Signed cookies** (``signed=True``): The value is HMAC-signed so any
  client-side tampering is detected on the next read.  Contents are still
  visible (Base64-encoded) in browser DevTools.
- **Encrypted cookies** (``encrypted=True``): The value is Fernet-encrypted,
  hiding the contents entirely.  Also requires ``pip install cryptography``.

Generate a strong key for production:

```sh
python -c "import secrets; print(secrets.token_hex(32))"
```

Set it before starting Mesop:

```sh
MESOP_COOKIE_SECRET_KEY=your-random-secret mesop main.py
```

Or in a `.env` file:

```sh title=".env"
MESOP_COOKIE_SECRET_KEY=your-random-secret
```

**Security notes:**

- Use a long, random value (32+ bytes of entropy).
- Rotate the key if it is ever compromised — all signed/encrypted cookies
  issued with the old key will become invalid on the next read (users will
  get default instances rather than an error).
- Never commit the key to source control.

**Multi-worker single-use behaviour:**

When ``me.set_cookie()`` is called, Mesop issues a short-lived signed token
that the browser exchanges for the actual ``Set-Cookie`` header.  The token
is single-use *within a single server process*: once a worker has seen a
token's nonce it will reject replays.  In multi-worker deployments, a
replay request routed to a *different* worker would be accepted because each
worker tracks used nonces independently.  In practice this is mitigated by
the CSRF ``Origin`` check on ``/__apply-cookies`` (cross-origin replay is
blocked) and the 60-second token TTL, but it is not cryptographically
guaranteed across workers.  If strict single-use across all workers is
required, ensure session affinity (sticky sessions) so that
``/__apply-cookies`` always returns to the originating worker.

## Usage Examples

### One-liner

You can specify the environment variables before the mesop command.

```sh
MESOP_STATE_SESSION_BACKEND=memory mesop main.py
```

### Use a .env file

Mesop also supports `.env` files. This is nice since you don't have to keep setting
the environment variables. In addition, the variables are only set when the application
is run.

```sh title=".env"
MESOP_STATE_SESSION_BACKEND=file
MESOP_STATE_SESSION_BACKEND_FILE_BASE_DIR=/tmp/mesop-sessions
```

When you run your Mesop app, the .env file will then be read.

```sh
mesop main.py
```
