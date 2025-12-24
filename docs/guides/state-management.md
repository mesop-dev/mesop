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

- https://github.com/mesop-dev/mesop/issues/565
- https://github.com/mesop-dev/mesop/issues/659
- https://github.com/mesop-dev/mesop/issues/814

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

## Tips

### State performance issues

Take a look at the [performance guide](./performance.md#optimizing-state-size) to learn how to identify and fix State-related performance issues.

## Next steps

Event handlers complement state management by providing a way to update your state in response to user interactions.

<a href="../event-handlers" class="next-step">
    Event handlers
</a>
