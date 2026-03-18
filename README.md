# whatamithinking-protolib

Foundational base classes and protocols for managing lifecycle state in Python objects, with clear, descriptive errors and support for both synchronous and asynchronous patterns.

- [Installation](#installation)
- [Overview](#overview)
- [Modules](#modules)
    - [Stateable](#stateable)
    - [Openable](#openable)
    - [Connectable](#connectable)
    - [Enableable](#enableable)
    - [Lockable](#lockable)
    - [Logable](#logable)
- [Combining Mixins](#combining-mixins)
- [License](#license)

---

## Installation

```bash
pip install whatamithinking-protolib
```

**Requires Python 3.12+**

`whatamithinking-aiotools` is installed automatically as a dependency (required by `AsyncLockable`).

---

## Overview

`protolib` provides a consistent pattern for objects with managed lifecycle states. Each module follows the same design:

- An **enum** describing the valid states.
- **Exception classes** that describe exactly what went wrong and why.
- **Guard decorators** (`ensure_*`) that protect methods from being called in an invalid state.
- **State-transition decorators** (`opener`, `connector`, etc.) that handle state changes automatically.
- **Abstract base classes** in both sync (`Openable`, `Connectable`, ...) and async (`AsyncOpenable`, `AsyncConnectable`, ...) variants.

```python
import whatamithinking.protolib as protolib
```

---

## Modules

### Stateable

`Stateable` is the common base class for all sync stateful mixins (`Openable`, `Connectable`, `Enableable`). It owns a single `_state_changed: threading.Condition` that every mixin on the same concrete object shares.

#### Why a shared condition?

Python's `threading.Condition` has no equivalent of `select()` — there is no way to block until _any one_ of several conditions is notified. If each mixin kept its own condition, code that needs to wait for a composite state change (e.g. "connected AND open") would be forced to poll. By sharing one condition across all state dimensions, a single `wait_for` call wakes on _any_ state mutation, regardless of which mixin triggered it:

```python
with obj._state_changed:
    obj._state_changed.wait_for(
        lambda: (
            obj.connection_state == protolib.ConnectionStateType.CONNECTED
            and obj.open_state == protolib.OpenStateType.OPEN
        )
    )
```

Every `_set_*_state` helper in `Connectable`, `Openable`, and `Enableable` acquires `_state_changed`, mutates its own state variable, and calls `notify_all()` — so all waiters are woken on every transition.

#### Lock integration

When the concrete class also inherits from `Lockable`, the condition is backed by `self.lock` (`threading.RLock`), consolidating all locking onto a single primitive.

---

### Openable

Manages an open/close lifecycle, suitable for resources like file handles, serial ports, or network sockets.

#### States — `OpenStateType`

| State     | Description                                      |
| --------- | ------------------------------------------------ |
| `CLOSED`  | Initial/default state. The object is not in use. |
| `OPENING` | Transitioning to open.                           |
| `OPEN`    | The object is open and operational.              |
| `CLOSING` | Transitioning to closed.                         |
| `ERROR`   | An error occurred during open or close.          |

#### Exceptions

| Exception        | Raised when...                                                |
| ---------------- | ------------------------------------------------------------- |
| `OpenStateError` | Base class for all open-state errors.                         |
| `NotOpenError`   | A method requires `OPEN` state but the object is not open.    |
| `NotClosedError` | `open()` was called but the object is not currently `CLOSED`. |
| `ClosedError`    | A method was called while the object is `CLOSED`.             |

#### Guard Decorators

These decorators check state before executing the method and raise an exception if the check fails.

| Decorator            | Raises if...                                           |
| -------------------- | ------------------------------------------------------ |
| `@ensure_open`       | Object is **not** in `OPEN` state → `NotOpenError`     |
| `@ensure_closed`     | Object is **not** in `CLOSED` state → `NotClosedError` |
| `@ensure_not_closed` | Object **is** in `CLOSED` state → `ClosedError`        |

Standalone check functions (`check_open`, `check_closed`, `check_not_closed`) are also available for use without decorators.

#### State-Transition Decorators

| Decorator | Usage                                                                                                                                  |
| --------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `@opener` | Apply to `open()`. Handles `OPENING` → `OPEN` (or `ERROR`) transitions. No-op if already `OPEN`. Requires object to be `CLOSED` first. |
| `@closer` | Apply to `close()`. Handles `CLOSING` → `CLOSED` (or `ERROR`) transitions. No-op if already `CLOSED`.                                  |

#### Base Classes

**`Openable`** — Synchronous. Implement `open()` and `close()`. Supports use as a context manager (`with`).

**`AsyncOpenable`** — Asynchronous. Implement `open()` and `close()` as coroutines. Supports use as an async context manager (`async with`).

#### State Condition Variable

`Openable` inherits `_state_changed: threading.Condition` from `Stateable`. It is acquired and `notify_all()` is called every time `_set_open_state()` runs, so other threads can reliably wait for a state transition:

```python
with obj._state_changed:
    obj._state_changed.wait_for(lambda: obj.open_state == protolib.OpenStateType.OPEN)
```

Because the condition is shared with all other `Stateable` mixins on the same object, a single `wait_for` call will also be woken by connection or enable state changes — no per-dimension polling needed. See [Stateable](#stateable) for details.

#### Example

```python
from typing import Optional
import whatamithinking.protolib as protolib


class MyResource(protolib.Openable):
    @protolib.opener
    def open(self, timeout: Optional[float] = None) -> None:
        # allocate resources here
        ...

    @protolib.closer
    def close(self, timeout: Optional[float] = None) -> None:
        # release resources here
        ...

    @protolib.ensure_open
    def read(self) -> bytes:
        # only runs when object is OPEN
        ...


# Using as a context manager
with MyResource() as r:
    data = r.read()

# Or manually
r = MyResource()
r.open()
try:
    data = r.read()
finally:
    r.close()
```

---

### Connectable

Manages a connect/disconnect lifecycle with support for polling-based keepalive, suitable for network clients, database connections, etc.

#### States — `ConnectionStateType`

| State           | Description                                   |
| --------------- | --------------------------------------------- |
| `DISCONNECTED`  | Initial/default state.                        |
| `CONNECTING`    | Transitioning to connected.                   |
| `CONNECTED`     | The object has an active connection.          |
| `DISCONNECTING` | Transitioning to disconnected.                |
| `ERROR`         | A connection or disconnection error occurred. |

#### Exceptions

| Exception               | Raised when...                                                         |
| ----------------------- | ---------------------------------------------------------------------- |
| `ConnectionError`       | Base class for all connection-related errors.                          |
| `NotConnectedError`     | A method requires `CONNECTED` state but is not connected.              |
| `NotDisconnectedError`  | `connect()` was called but the object is not `DISCONNECTED`.           |
| `NotBadConnectionError` | A method requires `DISCONNECTED` or `ERROR` state but neither applies. |
| `DisconnectedError`     | A method was called while the object is `DISCONNECTED`.                |

#### Guard Decorators

| Decorator                  | Raises if...                                                             |
| -------------------------- | ------------------------------------------------------------------------ |
| `@ensure_connected`        | Object is **not** `CONNECTED` → `NotConnectedError`                      |
| `@ensure_not_disconnected` | Object **is** `DISCONNECTED` → `DisconnectedError`                       |
| `@ensure_bad_connection`   | Object is **not** in `DISCONNECTED` or `ERROR` → `NotBadConnectionError` |

Standalone check functions (`check_connected`, `check_not_disconnected`, `check_bad_connection`) are also available.

#### State-Transition Decorators

| Decorator       | Usage                                                                                                                                           |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `@connector`    | Apply to `connect()`. Handles `CONNECTING` → `CONNECTED` (or `ERROR`) transitions. No-op if already `CONNECTED`. Requires `DISCONNECTED` state. |
| `@disconnector` | Apply to `disconnect()`. Handles `DISCONNECTING` → `DISCONNECTED` (or `ERROR`) transitions. No-op if already `DISCONNECTED`.                    |
| `@poller`       | Apply to `poll()`. Updates state to `CONNECTED` or `ERROR` based on the method's return value.                                                  |

#### Base Classes

**`Connectable`** — Synchronous. Implement `connect()`, `disconnect()`, and `poll()`. Supports use as a context manager. Includes a `keepalive()` method for smart polling.

**`AsyncConnectable`** — Asynchronous. Same interface with coroutines. Supports use as an async context manager.

#### State Condition Variable

`Connectable` inherits `_state_changed: threading.Condition` from `Stateable`. It is acquired and `notify_all()` is called every time `_set_connection_state()` runs, so other threads can reliably wait for a state transition:

```python
with obj._state_changed:
    obj._state_changed.wait_for(lambda: obj.connection_state == protolib.ConnectionStateType.CONNECTED)
```

Because the condition is shared with all other `Stateable` mixins on the same object, a single `wait_for` call will also be woken by open or enable state changes — no per-dimension polling needed. See [Stateable](#stateable) for details.

#### Keepalive

Both `Connectable` and `AsyncConnectable` include a `keepalive()` method. Set `connection_keepalive_timeout` (a `datetime.timedelta`) on the class, then call `keepalive()` periodically. It will only call `poll()` if the connection has not been used recently — avoiding redundant I/O.

```python
import datetime

class MyClient(protolib.Connectable):
    connection_keepalive_timeout = datetime.timedelta(seconds=30)

    @protolib.connector
    def connect(self, timeout=None): ...

    @protolib.disconnector
    def disconnect(self, timeout=None): ...

    @protolib.poller
    def poll(self, timeout=None) -> bool:
        # return True if connected, False otherwise
        return self._ping()
```

#### Example

```python
import whatamithinking.protolib as protolib


class DatabaseClient(protolib.Connectable):
    @protolib.connector
    def connect(self, timeout=None) -> None:
        # establish connection
        ...

    @protolib.disconnector
    def disconnect(self, timeout=None) -> None:
        # teardown connection
        ...

    @protolib.poller
    def poll(self, timeout=None) -> bool:
        # return True if still connected
        return self._ping()

    @protolib.ensure_connected
    def query(self, sql: str):
        ...


with DatabaseClient() as db:
    results = db.query("SELECT 1")
```

---

### Enableable

Manages an enable/disable lifecycle, suitable for toggling features or subsystems on and off.

#### States — `EnabledStateType`

| State       | Description                                 |
| ----------- | ------------------------------------------- |
| `DISABLED`  | Initial/default state.                      |
| `ENABLING`  | Transitioning to enabled.                   |
| `ENABLED`   | The object is enabled and operational.      |
| `DISABLING` | Transitioning to disabled.                  |
| `ERROR`     | An error occurred during enable or disable. |

#### Exceptions

| Exception           | Raised when...                                                     |
| ------------------- | ------------------------------------------------------------------ |
| `EnableableError`   | Base class for all enable-state errors.                            |
| `NotEnabledError`   | A method requires `ENABLED` state but the object is not enabled.   |
| `NotDisabledError`  | `enable()` was called but the object is not currently `DISABLED`.  |
| `NotBadEnableError` | A method requires `DISABLED` or `ERROR` state but neither applies. |
| `DisabledError`     | A method was called while the object is `DISABLED`.                |

#### Guard Decorators

| Decorator              | Raises if...                                                     |
| ---------------------- | ---------------------------------------------------------------- |
| `@ensure_enabled`      | Object is **not** `ENABLED` → `NotEnabledError`                  |
| `@ensure_not_disabled` | Object **is** `DISABLED` → `DisabledError`                       |
| `@ensure_bad_enable`   | Object is **not** in `DISABLED` or `ERROR` → `NotBadEnableError` |

Standalone check functions (`check_enabled`, `check_not_disabled`, `check_bad_enable`) are also available.

#### State-Transition Decorators

| Decorator   | Usage                                                                                                                                |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `@enabler`  | Apply to `enable()`. Handles `ENABLING` → `ENABLED` (or `ERROR`) transitions. No-op if already `ENABLED`. Requires `DISABLED` state. |
| `@disabler` | Apply to `disable()`. Handles `DISABLING` → `DISABLED` (or `ERROR`) transitions. No-op if already `DISABLED`.                        |

#### Base Classes

**`Enableable`** — Synchronous. Implement `enable()` and `disable()`.

**`AsyncEnableable`** — Asynchronous. Implement `enable()` and `disable()` as coroutines.

#### State Condition Variable

`Enableable` inherits `_state_changed: threading.Condition` from `Stateable`. It is acquired and `notify_all()` is called every time `_set_enabled_state()` runs, so other threads can reliably wait for a state transition:

```python
with obj._state_changed:
    obj._state_changed.wait_for(lambda: obj.enabled_state == protolib.EnabledStateType.ENABLED)
```

Because the condition is shared with all other `Stateable` mixins on the same object, a single `wait_for` call will also be woken by connection or open state changes — no per-dimension polling needed. See [Stateable](#stateable) for details.

#### Example

```python
import whatamithinking.protolib as protolib


class Subsystem(protolib.Enableable):
    @protolib.enabler
    def enable(self, timeout=None) -> None:
        # start up subsystem — state advances DISABLED → ENABLING → ENABLED (or ERROR)
        ...

    @protolib.disabler
    def disable(self, timeout=None) -> None:
        # shut down subsystem — state advances ENABLED → DISABLING → DISABLED (or ERROR)
        ...

    @protolib.ensure_enabled
    def run(self) -> None:
        # only runs when ENABLED
        ...

    @protolib.ensure_not_disabled
    def status(self) -> str:
        # runs in any state except DISABLED
        ...


# Wait for enabled from another thread
subsystem = Subsystem()
with subsystem._state_changed:
    subsystem._state_changed.wait_for(
        lambda: subsystem.enabled_state == protolib.EnabledStateType.ENABLED
    )
```

---

### Lockable

Provides thread-safe (or async-safe) locking for objects using a simple method decorator.

#### Decorator

| Decorator | Description                                                                                                                                       |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `@locked` | Acquires the object's lock before executing the method and releases it when done. Works with sync, async, generator, and async generator methods. |

#### Base Classes

**`Lockable`** — Synchronous. Uses a `threading.RLock` (reentrant). Pass a custom `lock` to `__init__`, or one is created automatically.

**`AsyncLockable`** — Asynchronous. Uses an `aiotools.RLock` (reentrant). Pass a custom `lock` to `__init__`, or one is created automatically.

#### Example

```python
import whatamithinking.protolib as protolib


class SafeCounter(protolib.Lockable):
    def __init__(self):
        super().__init__()
        self._count = 0

    @protolib.locked
    def increment(self):
        self._count += 1

    @protolib.locked
    def value(self) -> int:
        return self._count
```

---

### Logable

Provides a structured logging interface built on Python's standard `logging` module.

#### `LogLevelType`

An enum mirroring standard log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

#### Base Class — `Logable`

Pass a `log_name` to `__init__` to configure a named logger with a `NullHandler` (following best practices for libraries). Logging output is controlled by the consumer of the library.

| Method                       | Description                                                                                    |
| ---------------------------- | ---------------------------------------------------------------------------------------------- |
| `_log(level, msg, **kwargs)` | Log a message at the given level with any extra context.                                       |
| `_log_extra()`               | Override to return a dict of additional metadata included in every log record for this object. |

At `ERROR` level or above, `exc_info` is automatically captured.

#### Example

```python
import whatamithinking.protolib as protolib


class MyService(protolib.Logable):
    def __init__(self):
        super().__init__(log_name="myservice")

    def do_work(self):
        self._log(protolib.LogLevelType.INFO, "Starting work")
        try:
            ...
        except Exception:
            self._log(protolib.LogLevelType.ERROR, "Work failed")
            raise
```

---

## Combining Mixins

All base classes are implemented with cooperative multiple inheritance (`super().__init__(**kwargs)`), so they can be freely combined. When mixing multiple stateful classes (`Openable`, `Connectable`, `Enableable`), their shared `Stateable` base is initialised exactly once by the MRO, producing a single `_state_changed` condition covering all state dimensions on the object:

```python
import whatamithinking.protolib as protolib


class MyDevice(protolib.Openable, protolib.Lockable, protolib.Logable):
    def __init__(self):
        super().__init__(log_name="mydevice")

    @protolib.opener
    def open(self, timeout=None) -> None:
        self._log(protolib.LogLevelType.INFO, "Opening device")
        ...

    @protolib.closer
    def close(self, timeout=None) -> None:
        self._log(protolib.LogLevelType.INFO, "Closing device")
        ...

    @protolib.locked
    @protolib.ensure_open
    def read(self) -> bytes:
        ...
```

### `leaf_method`

The `@leaf_method` utility ensures that state-transition decorators (like `@opener`, `@connector`, `@enabler`) only execute their wrapping logic at the **leaf (most-derived) class** in an inheritance chain. This means intermediate `super().open()` calls in a subclass hierarchy won't trigger redundant state transitions — only the outermost call does.

---

## License

MIT — see [LICENSE](LICENSE).
