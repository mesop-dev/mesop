# State Management

State management is a critical element of building interactive apps because it allows you store information about what the user did in a structured way.

## Basic usage

You can register a class using the class decorator `me.stateclass` which is like a dataclass with special powers:

```python
@me.stateclass
class State:
  val: str
```

You can get an instance of the state class inside any of your Mesop component functions by using `me.state`:

```py
@me.page()
def page():
    state = me.state(State)
    me.text(state.val)
```

## Use immutable default values

Similar to [regular dataclasses which disallow mutable default values](https://docs.python.org/3/library/dataclasses.html#mutable-default-values), you need to avoid mutable default values such as list and dict for state classes. Using mutable default values can result in leaking state across sessions which can be a serious privacy issue.

You **MUST** use immutable default values _or_ use dataclasses `field` initializer _or_ not set a default value.

???+ success "Good: immutable default value"
      Setting a default value to an immutable type like str is OK.

      ```py
      @me.stateclass
      class State:
        a: str = "abc"
      ```

???+ failure "Bad: mutable default value"

    The following will raise an exception because dataclasses prevents you from using mutable collection types like `list` as the default value because this is a common footgun.

    ```py
    @me.stateclass
    class State:
      a: list[str] = ["abc"]
    ```

    If you set a default value to an instance of a custom type, an exception will not be raised, but you will be dangerously sharing the same mutable instance across sessions which could cause a serious privacy issue.

    ```py
    @me.stateclass
    class State:
      a: MutableClass = MutableClass()
    ```

???+ success "Good: default factory"

    If you want to set a field to a mutable default value, use default_factory in the `field`  function from the dataclasses module to create a new instance of the mutable default value for each instance of the state class.

    ```py
    from dataclasses import field

    @me.stateclass
    class State:
      a: list[str] = field(default_factory=lambda: ["abc"])
    ```

???+ success "Good: no default value"

    If you want a default of an empty list, you can just not define a default value and Mesop will automatically define an empty list default value.

    For example, if you write the following:

    ```py
    @me.stateclass
    class State:
      a: list[str]
    ```

    It's the equivalent of:

    ```py
    @me.stateclass
    class State:
      a: list[str] = field(default_factory=list)
    ```

## How State Works

`me.stateclass` is a class decorator which tells Mesop that this class can be retrieved using the `me.state` method, which will return the state instance for the current user session.

> If you are familiar with the dependency injection pattern, Mesop's stateclass and state API is essentially a minimalist dependency injection system which scopes the state object to the lifetime of a user session.

Under the hood, Mesop is sending the state back and forth between the server and browser client so everything in a state class must be serializable.

## Serialization

Understanding what can and cannot be serialized in Mesop state is critical to avoiding runtime errors. This section explains which types are supported and provides guidance on handling complex objects.

### Serializable Types

Mesop supports serialization for the following types:

#### Primitive Types
- `int` - Integer numbers
- `float` - Floating-point numbers
- `str` - Strings
- `bool` - Boolean values

```python
@me.stateclass
class State:
  count: int
  temperature: float
  name: str
  is_enabled: bool
```

#### Collections
- `list[T]` - Lists (including nested lists)
- `dict[K, V]` - Dictionaries (including nested dicts)
- `set[T]` - Sets

```python
@me.stateclass
class State:
  items: list[str]
  scores: dict[str, int]
  unique_ids: set[int]
  nested_list: list[list[str]]
  nested_dict: dict[str, dict[str, bool]]
```

#### Date and Time
- `datetime.datetime` - Date and time objects
- `datetime.date` - Date objects

```python
from datetime import datetime, date

@me.stateclass
class State:
  created_at: datetime
  birthday: date
```

#### Binary Data
- `bytes` - Binary data

```python
@me.stateclass
class State:
  file_content: bytes
```

#### Special Types
- `pandas.DataFrame` - Pandas DataFrames (requires pandas to be installed)
- `pydantic.BaseModel` - Pydantic models and subclasses
- `mesop.components.uploader.UploadedFile` - Uploaded files from the uploader component

```python
import pandas as pd
from pydantic import BaseModel

class UserModel(BaseModel):
  name: str
  age: int

@me.stateclass
class State:
  data_frame: pd.DataFrame
  user: UserModel
```

#### Nested State Classes
You can nest dataclasses within your state class, and they will be automatically serialized:

```python
from dataclasses import dataclass

@dataclass
class Address:
  street: str
  city: str

@me.stateclass
class State:
  address: Address
  addresses: list[Address]
```

### Non-Serializable Types

Most types that are not in the serializable types list above cannot be serialized. This includes (but is not limited to):

- Functions, lambdas, and methods
- File handles, sockets, and I/O objects
- Database connections and cursors
- Thread and lock objects
- Protocol buffers and custom complex objects

**If you get a serialization error**, refer to the [serializable types](#serializable-types) section above for supported types.

### Workarounds for Unsupported Types

If you need to work with types that aren't directly serializable, here are some strategies:

#### 1. Break down into primitives

Extract the data you need into serializable primitive types:

```python
# ❌ Bad: storing complex object
@me.stateclass
class State:
  api_response: requests.Response  # Not serializable

# ✅ Good: extract the data you need
@me.stateclass
class State:
  response_text: str
  status_code: int
  headers: dict[str, str]

def on_click(e: me.ClickEvent):
  state = me.state(State)
  response = requests.get("https://api.example.com")
  state.response_text = response.text
  state.status_code = response.status_code
  state.headers = dict(response.headers)
```

#### 2. Serialize to JSON or bytes

Convert complex objects to JSON strings or bytes:

```python
@me.stateclass
class State:
  config_json: str  # Store as JSON string

def on_load(e: me.LoadEvent):
  state = me.state(State)
  complex_config = load_complex_config()
  state.config_json = json.dumps(complex_config)

def use_config():
  state = me.state(State)
  config = json.loads(state.config_json)
  # Use config...
```

#### 3. Use Pydantic models

Pydantic models are serializable and can handle complex nested structures:

```python
from pydantic import BaseModel

class UserProfile(BaseModel):
  name: str
  email: str
  settings: dict[str, str]
  created_at: datetime

@me.stateclass
class State:
  profile: UserProfile  # Pydantic models are serializable

def on_login(e: me.ClickEvent):
  state = me.state(State)
  # Pydantic can serialize most Python types
  state.profile = UserProfile(
    name="Alice",
    email="alice@example.com",
    settings={"theme": "dark"},
    created_at=datetime.now()
  )
```

> **Note**: When using Pydantic models, you get less granular state diffing compared to using primitives directly. This is fine if you don't store a large amount of state data.

### Known Issues

Be aware of these known serialization limitations:

- [https://github.com/mesop-dev/mesop/issues/565](https://github.com/mesop-dev/mesop/issues/565)
- [https://github.com/mesop-dev/mesop/issues/659](https://github.com/mesop-dev/mesop/issues/659)
- [https://github.com/mesop-dev/mesop/issues/814](https://github.com/mesop-dev/mesop/issues/814)

## Multiple state classes

You can use multiple classes to store state for the current user session.

Using different state classes for different pages or components can help make your app easier to maintain and more modular.

```py
@me.stateclass
class PageAState:
    ...

@me.stateclass
class PageBState:
    ...

@me.page(path="/a")
def page_a():
    state = me.state(PageAState)
    ...

@me.page(path="/b")
def page_b():
    state = me.state(PageBState)
    ...
```

Under the hood, Mesop is managing state classes based on the identity (e.g. module name and class name) of the state class, which means that you could have two state classes named "State", but if they are in different modules, then they will be treated as separate state, which is what you would expect.

## Nested State

You can also have classes inside of a state class as long as everything is serializable:

```python
class NestedState:
  val: str

@me.stateclass
class State:
  nested: NestedState

def app():
  state = me.state(State)
```

> Note: you only need to decorate the top-level state class with `@me.stateclass`. All the nested state classes will automatically be wrapped.

### Nested State and dataclass

Sometimes, you may want to explicitly decorate the nested state class with `dataclass` because in the previous example, you couldn't directly instantiate `NestedState`.

If you wanted to use NestedState as a general dataclass, you can do the following:

```python
@dataclass
class NestedState:
  val: str = ""

@me.stateclass
class State:
  nested: NestedState

def app():
  state = me.state(State)
```

> Reminder: because dataclasses do not have default values, you will need to explicitly set default values, otherwise Mesop will not be able to instantiate an empty version of the class.

Now, if you have an event handler function, you can do the following:

```py
def on_click(e):
    response = call_api()
    state = me.state(State)
    state.nested = NestedState(val=response.text)
```

If you didn't explicitly annotate NestedState as a dataclass, then you would get an error instantiating NestedState because there's no initializer defined.

## Security & Best Practices

### Validate input before updating state

Event handlers receive data directly from the browser. Always validate and sanitize that data before writing it into state. Trusting it blindly can lead to corrupt state or unexpected behaviour.

???+ failure "Bad: storing unvalidated input"

    ```python
    def on_submit(e: me.ClickEvent):
        state = me.state(State)
        # Directly copying user-supplied value with no checks
        state.age = int(state.age_input)   # crashes if input is not a number
        state.email = state.email_input    # no format validation
    ```

???+ success "Good: validate before writing to state"

    ```python
    def on_submit(e: me.ClickEvent):
        state = me.state(State)

        # Validate age
        try:
            age = int(state.age_input)
        except ValueError:
            state.error = "Age must be a number."
            return
        if age < 0 or age > 150:
            state.error = "Age must be between 0 and 150."
            return

        # Validate email (basic check)
        if "@" not in state.email_input or "." not in state.email_input:
            state.error = "Enter a valid email address."
            return

        state.age = age
        state.email = state.email_input
        state.error = ""
    ```

This is especially important for fields that end up in database queries, file paths, or external API calls.

### Validate state before sending to external services

State holds what the user submitted across one or more interactions. Before passing state values to a database, API, or any external service, validate them again at the point of use. Never assume that because data is in state it is already safe.

???+ failure "Bad: using state values directly in a database call"

    ```python
    def on_save(e: me.ClickEvent):
        state = me.state(State)
        # No validation — anything could be in state.username
        db.execute("INSERT INTO users (name) VALUES (?)", (state.username,))
    ```

???+ success "Good: re-validate at the service boundary"

    ```python
    import re

    def on_save(e: me.ClickEvent):
        state = me.state(State)

        username = state.username.strip()
        if not username or not re.match(r"^[a-zA-Z0-9_]{3,30}$", username):
            state.error = "Username must be 3–30 alphanumeric characters."
            return

        db.execute("INSERT INTO users (name) VALUES (?)", (username,))
    ```

Use an ORM or parameterised queries to avoid SQL injection. If you call an external HTTP API, validate that URLs or IDs embedded in state are well-formed before constructing the request.

### Be careful what you store in state

Mesop serializes state and sends it between the server and the browser on every interaction. This has two important consequences:

**State is visible to the client.** The serialized state travels over the network and can be inspected by a determined user. Do not store secrets, private keys, raw passwords, or other sensitive credentials in state.

???+ failure "Bad: storing a secret in state"

    ```python
    @me.stateclass
    class State:
        api_key: str          # ❌ Will be sent to the browser
        password_hash: str    # ❌ Leaks implementation details
    ```

???+ success "Good: keep secrets server-side"

    ```python
    import os

    # Read once at startup and keep in server memory, not in state
    _API_KEY = os.environ["MY_API_KEY"]

    @me.stateclass
    class State:
        is_authenticated: bool   # ✅ Only the outcome goes in state

    def call_api():
        # Use the module-level constant, never state
        return requests.get("https://api.example.com", headers={"Authorization": _API_KEY})
    ```

**State size affects performance.** Everything in state is serialized and sent on every round-trip. Avoid storing large blobs, full API responses, or entire datasets. Store only the minimum data needed to render the UI. See the [performance guide](./performance.md#optimizing-state-size) for details.

???+ failure "Bad: storing a full API response"

    ```python
    @me.stateclass
    class State:
        raw_response: str   # ❌ Could be megabytes of JSON
    ```

???+ success "Good: store only what the UI needs"

    ```python
    @me.stateclass
    class State:
        result_count: int
        result_titles: list[str]   # ✅ Just the fields displayed
    ```

**State is not a substitute for authentication.** State is scoped to a user session, but Mesop itself does not authenticate users. Do not rely on a flag like `state.is_admin = True` as your sole access control mechanism. Enforce authorization on the server side (e.g., check the session token in your event handler) before performing privileged operations.

???+ failure "Bad: trusting state for authorization"

    ```python
    def on_delete(e: me.ClickEvent):
        state = me.state(State)
        if state.is_admin:   # ❌ Client can manipulate this
            db.delete_all()
    ```

???+ success "Good: verify authorization server-side"

    ```python
    def on_delete(e: me.ClickEvent):
        state = me.state(State)
        user = get_current_user(state.session_token)
        if not user or not user.has_permission("delete"):
            state.error = "Permission denied."
            return
        db.delete_all()
    ```

**State does not persist across sessions.** When a user's session ends (e.g., they close the tab or the server restarts), state is lost. Do not use state as durable storage. Persist anything important — user preferences, saved work, etc. — to a database or other backend store before the session ends.

## Tips

### State performance issues

Take a look at the [performance guide](./performance.md#optimizing-state-size) to learn how to identify and fix State-related performance issues.

## Next steps

Event handlers complement state management by providing a way to update your state in response to user interactions.

<a href="../event-handlers" class="next-step">
    Event handlers
</a>
