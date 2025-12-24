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
- `tuple[T, ...]` - Tuples

```python
@me.stateclass
class State:
  items: list[str]
  scores: dict[str, int]
  unique_ids: set[int]
  nested_list: list[list[str]]
  nested_dict: dict[str, dict[str, bool]]
  coordinates: tuple[float, float]
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

The following types **cannot** be serialized and will cause errors if used in state:

#### Functions and Lambdas
Functions, methods, and lambda expressions cannot be serialized.

???+ failure "Bad: function in state"
    ```python
    @me.stateclass
    class State:
      callback: Callable  # ❌ Will fail
    ```

???+ success "Good: use event handlers"
    Instead of storing functions in state, use Mesop's event handler pattern:
    
    ```python
    @me.stateclass
    class State:
      value: str
    
    def on_click(e: me.ClickEvent):
      state = me.state(State)
      state.value = "clicked"
    
    def app():
      me.button("Click", on_click=on_click)
    ```

#### File Handles and I/O Objects
Open files, sockets, and other I/O objects cannot be serialized.

???+ failure "Bad: file handle in state"
    ```python
    @me.stateclass
    class State:
      file: io.TextIOWrapper  # ❌ Will fail
    ```

???+ success "Good: read file contents"
    Read the file contents into a serializable format:
    
    ```python
    @me.stateclass
    class State:
      file_content: str
    
    def on_upload(e: me.UploadEvent):
      state = me.state(State)
      # Use the file property for convenience with single uploads
      if e.file:
        state.file_content = e.file.getvalue().decode('utf-8')
    ```

#### Database Connections and ORM Objects
Database connections, cursors, and ORM session objects cannot be serialized.

???+ failure "Bad: database connection in state"
    ```python
    @me.stateclass
    class State:
      db_connection: sqlite3.Connection  # ❌ Will fail
      session: sqlalchemy.orm.Session  # ❌ Will fail
    ```

???+ success "Good: recreate connections as needed"
    Create database connections inside event handlers or use connection pooling:
    
    ```python
    @me.stateclass
    class State:
      user_data: dict[str, str]
    
    def on_load(e: me.LoadEvent):
      state = me.state(State)
      # Create connection when needed
      conn = get_db_connection()
      state.user_data = fetch_user_data(conn)
      conn.close()
    ```

#### Thread and Lock Objects
Threading primitives like threads, locks, and queues cannot be serialized.

???+ failure "Bad: thread objects in state"
    ```python
    @me.stateclass
    class State:
      thread: threading.Thread  # ❌ Will fail
      lock: threading.Lock  # ❌ Will fail
    ```

#### Protocol Buffers and Complex Objects
Protocol buffer messages and other complex objects that don't have built-in serialization support cannot be used.

> Note: This example uses Mesop's internal proto definitions for illustration. The same principle applies to any protocol buffer or complex object type.

???+ failure "Bad: protocol buffer in state"
    ```python
    # Example using protocol buffer (not recommended)
    import mesop.protos.ui_pb2 as pb
    
    @me.stateclass
    class State:
      proto: pb.Style  # ❌ Will fail
    ```

???+ success "Good: extract serializable data"
    Extract the data you need into serializable types:
    
    ```python
    @me.stateclass
    class State:
      style_config: dict[str, str]
    
    def on_update(e: me.ClickEvent):
      state = me.state(State)
      # If you receive a proto from an API, extract the data
      # proto = some_api_call()  # Returns a protobuf
      # Extract only what you need into serializable types
      state.style_config = {"color": "blue", "font": "Arial"}
    ```

### Troubleshooting Serialization Errors

If you encounter a serialization error, you'll typically see an error message like:

```
Object of type <Type> is not JSON serializable
```

**Steps to fix:**

1. **Identify the problematic field**: Look at the error message to determine which field is causing the issue.

2. **Check the type**: Verify that the field type is in the list of serializable types above.

3. **Extract serializable data**: If you need to store complex objects, extract only the serializable data you need:

```python
# Instead of storing the entire object
@me.stateclass
class State:
  api_response: requests.Response  # ❌ Not serializable

# Extract only what you need
@me.stateclass
class State:
  response_text: str
  status_code: int

def on_click(e: me.ClickEvent):
  state = me.state(State)
  response = requests.get("https://api.example.com")
  state.response_text = response.text
  state.status_code = response.status_code
```

4. **Use temporary variables**: For objects needed only during event handling, use local variables instead of state:

```python
def on_process(e: me.ClickEvent):
  state = me.state(State)
  
  # Use locally, don't store in state
  connection = database.connect()
  data = connection.query("SELECT * FROM users")
  connection.close()
  
  # Store only the results
  state.users = [{"id": row[0], "name": row[1]} for row in data]
```

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
