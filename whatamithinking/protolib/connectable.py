from abc import abstractmethod, ABC
from enum import Enum
import inspect
from typing import *
import functools
import datetime

from .stateable import Stateable
from .util import leaf_method

__all__ = [
    "ConnectionStateType",
    "ConnectionError",
    "NotConnectedError",
    "NotBadConnectionError",
    "NotDisconnectedError",
    "check_connected",
    "ensure_connected",
    "check_bad_connection",
    "ensure_bad_connection",
    "check_not_disconnected",
    "ensure_not_disconnected",
    "connector",
    "disconnector",
    "poller",
    "Connectable",
    "AsyncConnectable",
]


T = TypeVar("T")
P = ParamSpec("P")


class ConnectionStateType(str, Enum):
    ERROR = "error"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"


class ConnectionError(Exception):
    """Base exception for connection-related issues."""


class NotConnectedError(ConnectionError):
    """Raised when attempt made to call a method on an object when it
    is not currently in a connected state."""


class NotBadConnectionError(ConnectionError):
    """Raised when attempt made to call a method on an object when it
    is not currently in a disconnected or error state."""


class NotDisconnectedError(ConnectionError):
    """Raised when attempt made to connect an object when it
    is not currently in a disconnected state."""


class DisconnectedError(Exception):
    """Raised when attempt made to use an object which is disconnected."""


def check_connected(obj: Union["AsyncConnectable", "Connectable"]) -> None:
    """Check if the given object is in CONNECTED state and raise an exception, NotConnectedError,
    if not."""
    if not isinstance(obj, (AsyncConnectable, Connectable)):
        raise TypeError(
            f"AsyncConnectable or Connectable expected, but {type(obj)} given."
        )
    if obj._connection_state != ConnectionStateType.CONNECTED:
        raise NotConnectedError(
            f"Cannot perform the operation while not "
            + f"in {ConnectionStateType.CONNECTED} state."
        )


def ensure_connected(method: Callable[P, T]) -> Callable[P, T]:
    """Decorator to check if the method's object is in CONNECTED state and raise an exception,
    NotConnectedError, if not."""
    if inspect.iscoroutinefunction(method):

        @functools.wraps(method)
        async def _ensure_connected(self, *args: P.args, **kwargs: P.kwargs) -> T:
            check_connected(self)
            return await method(self, *args, **kwargs)

    elif inspect.isasyncgenfunction(method):

        @functools.wraps(method)
        async def _ensure_connected(
            self, *args: P.args, **kwargs: P.kwargs
        ) -> AsyncIterator[T]:
            check_connected(self)
            async for _ in method(self, *args, **kwargs):
                yield _

    elif inspect.isgeneratorfunction(method):

        @functools.wraps(method)
        def _ensure_connected(self, *args: P.args, **kwargs: P.kwargs) -> Iterator[T]:
            check_connected(self)
            yield from method(self, *args, **kwargs)

    else:

        @functools.wraps(method)
        def _ensure_connected(self, *args: P.args, **kwargs: P.kwargs) -> T:
            check_connected(self)
            return method(self, *args, **kwargs)

    return _ensure_connected


def check_not_disconnected(obj: Union["AsyncConnectable", "Connectable"]) -> None:
    """Check if the given object is in DISCONNECTED state and raise an exception, DisconnectedError,
    if so."""
    if not isinstance(obj, (AsyncConnectable, Connectable)):
        raise TypeError(
            f"AsyncConnectable or Connectable expected, but {type(obj)} given."
        )
    if obj._connection_state == ConnectionStateType.DISCONNECTED:
        raise DisconnectedError(
            f"Cannot perform operation while in {ConnectionStateType.DISCONNECTED} state."
        )


def ensure_not_disconnected(method: Callable[P, T]) -> Callable[P, T]:
    """Decorator to check if the object is in DISCONNECTED state and raise an exception,
    DisconnectedError, if so."""
    if inspect.iscoroutinefunction(method):

        @functools.wraps(method)
        async def _ensure_not_disconnected(
            self, *args: P.args, **kwargs: P.kwargs
        ) -> T:
            check_not_disconnected(self)
            return await method(self, *args, **kwargs)

    elif inspect.isasyncgenfunction(method):

        @functools.wraps(method)
        async def _ensure_not_disconnected(
            self, *args: P.args, **kwargs: P.kwargs
        ) -> AsyncIterator[T]:
            check_not_disconnected(self)
            async for _ in method(self, *args, **kwargs):
                yield _

    elif inspect.isgeneratorfunction(method):

        @functools.wraps(method)
        def _ensure_not_disconnected(
            self, *args: P.args, **kwargs: P.kwargs
        ) -> Iterator[T]:
            check_not_disconnected(self)
            yield from method(self, *args, **kwargs)

    else:

        @functools.wraps(method)
        def _ensure_not_disconnected(self, *args: P.args, **kwargs: P.kwargs) -> T:
            check_not_disconnected(self)
            return method(self, *args, **kwargs)

    return _ensure_not_disconnected


def check_bad_connection(obj: Union["AsyncConnectable", "Connectable"]) -> None:
    """Check if the given object is in DISCONNECTED or ERROR state
    and raise an exception, NotBadConnectionError, if not."""
    if not isinstance(obj, (AsyncConnectable, Connectable)):
        raise TypeError(
            f"AsyncConnectable or Connectable expected, but {type(obj)} given."
        )
    if not obj._connection_state in (
        ConnectionStateType.DISCONNECTED,
        ConnectionStateType.ERROR,
    ):
        raise NotBadConnectionError(
            f"Cannot perform the operation while not "
            f"in {ConnectionStateType.DISCONNECTED} or {ConnectionStateType.ERROR} state."
        )


def ensure_bad_connection(method: Callable[P, T]) -> Callable[P, T]:
    """Decorator to check if the object is in DISCONNECTED or ERROR state
    and raise an exception, NotBadConnectionError, if not."""
    if inspect.iscoroutinefunction(method):

        @functools.wraps(method)
        async def _ensure_bad_connection(self, *args: P.args, **kwargs: P.kwargs) -> T:
            check_bad_connection(self)
            return await method(self, *args, **kwargs)

    elif inspect.isasyncgenfunction(method):

        @functools.wraps(method)
        async def _ensure_bad_connection(
            self, *args: P.args, **kwargs: P.kwargs
        ) -> AsyncIterator[T]:
            check_bad_connection(self)
            async for _ in method(self, *args, **kwargs):
                yield _

    elif inspect.isgeneratorfunction(method):

        @functools.wraps(method)
        def _ensure_bad_connection(
            self, *args: P.args, **kwargs: P.kwargs
        ) -> Iterator[T]:
            check_bad_connection(self)
            yield from method(self, *args, **kwargs)

    else:

        @functools.wraps(method)
        def _ensure_bad_connection(self, *args: P.args, **kwargs: P.kwargs) -> T:
            check_bad_connection(self)
            return method(self, *args, **kwargs)

    return _ensure_bad_connection


@leaf_method
def connector(method: Callable[P, T]) -> T:
    """Decorator for connect method to handle state changes.

    If already in a connected state, a method using this decorator
    returns immediately without running the method.
    """
    if inspect.iscoroutinefunction(method):

        @functools.wraps(method)
        async def _connector(self, *args: P.args, **kwargs: P.kwargs) -> T:
            if self.connection_state == ConnectionStateType.CONNECTED:
                return
            if self.connection_state != ConnectionStateType.DISCONNECTED:
                raise NotDisconnectedError(
                    "The operation cannot be performed unless "
                    + f"in a {ConnectionStateType.DISCONNECTED} state."
                )
            await self._set_connection_state(ConnectionStateType.CONNECTING)
            try:
                result = await method(self, *args, **kwargs)
            except:
                await self._set_connection_state(ConnectionStateType.ERROR)
                raise
            else:
                await self._set_connection_state(ConnectionStateType.CONNECTED)
                return result
            finally:
                await self._set_connection_last_used()

    else:

        @functools.wraps(method)
        def _connector(self, *args: P.args, **kwargs: P.kwargs) -> T:
            if self.connection_state == ConnectionStateType.CONNECTED:
                return
            if self.connection_state != ConnectionStateType.DISCONNECTED:
                raise NotDisconnectedError(
                    "The operation cannot be performed unless "
                    + f"in a {ConnectionStateType.DISCONNECTED} state."
                )
            self._set_connection_state(ConnectionStateType.CONNECTING)
            try:
                result = method(self, *args, **kwargs)
            except:
                self._set_connection_state(ConnectionStateType.ERROR)
                raise
            else:
                self._set_connection_state(ConnectionStateType.CONNECTED)
                return result
            finally:
                self._set_connection_last_used()

    return _connector


@leaf_method
def disconnector(method: Callable[P, T]) -> T:
    """Decorator for disconnect method to handle state changes."""
    if inspect.iscoroutinefunction(method):

        @functools.wraps(method)
        async def _disconnector(self, *args: P.args, **kwargs: P.kwargs) -> T:
            if self.connection_state == ConnectionStateType.DISCONNECTED:
                return
            await self._set_connection_state(ConnectionStateType.DISCONNECTING)
            try:
                result = await method(self, *args, **kwargs)
            except:
                await self._set_connection_state(ConnectionStateType.ERROR)
                raise
            else:
                await self._set_connection_state(ConnectionStateType.DISCONNECTED)
                return result
            finally:
                await self._set_connection_last_used()

    else:

        @functools.wraps(method)
        def _disconnector(self, *args: P.args, **kwargs: P.kwargs) -> T:
            if self.connection_state == ConnectionStateType.DISCONNECTED:
                return
            self._set_connection_state(ConnectionStateType.DISCONNECTING)
            try:
                result = method(self, *args, **kwargs)
            except:
                self._set_connection_state(ConnectionStateType.ERROR)
                raise
            else:
                self._set_connection_state(ConnectionStateType.DISCONNECTED)
                return result
            finally:
                self._set_connection_last_used()

    return _disconnector


@leaf_method
def poller(method: Callable[P, T]) -> T:
    """Decorator for poll method to handle state changes."""
    if inspect.iscoroutinefunction(method):

        @functools.wraps(method)
        async def _poller(self, *args: P.args, **kwargs: P.kwargs) -> T:
            try:
                success = await method(self, *args, **kwargs)
            except:
                success = False
                raise
            finally:
                # set to error state so caller forced to first call disconnect
                # before calling connect, so cleanup is performed
                state = (
                    ConnectionStateType.CONNECTED
                    if success
                    else ConnectionStateType.ERROR
                )
                if self.connection_state != state:
                    await self._set_connection_state(state)
                await self._set_connection_last_used()
            return success

    else:

        @functools.wraps(method)
        def _poller(self, *args: P.args, **kwargs: P.kwargs) -> T:
            try:
                success = method(self, *args, **kwargs)
            except:
                success = False
                raise
            finally:
                # set to error state so caller forced to first call disconnect
                # before calling connect, so cleanup is performed
                state = (
                    ConnectionStateType.CONNECTED
                    if success
                    else ConnectionStateType.ERROR
                )
                if self.connection_state != state:
                    self._set_connection_state(state)
                self._set_connection_last_used()
            return success

    return _poller


class Connectable(Stateable, ABC):
    """Sync connect/disconnect/poll interface.

    Inherits from :class:`~.stateable.Stateable` so that ``_state_changed`` is shared
    with any other ``Stateable`` mixins (e.g. ``Openable``, ``Enableable``) on the same
    concrete class.  This means a single ``_state_changed.wait()`` call is sufficient
    to observe *any* state change on the object.

    State transitions are performed by ``_set_connection_state``, which holds
    ``_state_changed`` across the mutation and calls ``notify_all()`` so that all
    threads waiting on the condition are woken.
    """

    connection_keepalive_timeout: datetime.timedelta | None = None
    _connection_state: ConnectionStateType = ConnectionStateType.DISCONNECTED
    _connection_last_used: datetime.datetime | None = None

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def __enter__(self) -> Self:
        """Open the connection, calling the `connect` method."""
        try:
            self.connect()
        except:  # context manager should always cleanup, but __exit__ wont be called
            # because we did not enter successfully
            self.disconnect()
            raise
        return self

    def __exit__(self, *args) -> None:
        """Close the connection, calling the `disconnect` method."""
        self.disconnect()

    def _set_connection_state(self, state: "ConnectionStateType") -> None:
        """Set the connection state and notify all waiters on ``_state_changed``."""
        with self._state_changed:
            self._connection_state = state
            self._state_changed.notify_all()

    @property
    def connection_state(self) -> "ConnectionStateType":
        """Return enum for the current connection state."""
        return self._connection_state

    def _set_connection_last_used(
        self, last_used: datetime.datetime | None = None
    ) -> None:
        """Set the last contact time for the connection.

        This should be called anytime a connection is used to minimize unnecessary polling
        is using the `keepalive` method.

        Args:
            last_used: Optional. If not given, defaults to current datetime. This datetime
                must be timezone aware.
        """
        self._connection_last_used = last_used or datetime.datetime.now().astimezone()

    @property
    def connection_last_used(self) -> datetime.datetime | None:
        """Return last datetime when communication was made successfully using this connection."""
        return self._connection_last_used

    @abstractmethod
    def connect(self, timeout: Optional[float] = None) -> None:
        """Attempt a connection to/for the object, which can be cancelled
        if it takes too long."""

    @abstractmethod
    def disconnect(self, timeout: Optional[float] = None) -> None:
        """Disconnect for/from the object. Cannot be cancelled."""

    @abstractmethod
    def poll(self, timeout: Optional[float] = None) -> bool:
        """Poll to check the connection status, returning True for
        connected and False for disconnected."""

    def keepalive(self) -> None:
        """Keep the connection alive by polling, but only when in a CONNECTED state and only when
        the connection has not been used in a while.

        Default implementation checks the connection state first and if not CONNECTED, it is a no-op.
        If CONNECTED, it checks the `connection_last_used` property and only polls
        if the value is None or if last contact was made more than `connection_keepalive_timeout`
        ago from current time.

        This allows for `smart polling` that reduces unnecessary IO when we already have
        recent communication which confirms the connection state and reduces chance of background
        keepalive tasks from potentially interrupting ongoing communications in another thread/task.
        """
        if self.connection_state != ConnectionStateType.CONNECTED:
            return
        if self.connection_keepalive_timeout is None:
            raise RuntimeError(
                "connection_keepalive_timeout set to None, but must be set to datetime.timedelta."
            )
        last_used = self.connection_last_used
        if (
            last_used is not None
            and (datetime.datetime.now().astimezone() - last_used)
            < self.connection_keepalive_timeout
        ):
            return
        self.poll()


class AsyncConnectable(ABC):
    """Async connect/disconnect/poll interface."""

    connection_keepalive_timeout: datetime.timedelta | None = None
    _connection_state: ConnectionStateType = ConnectionStateType.DISCONNECTED
    _connection_last_used: datetime.datetime | None = None

    async def __aenter__(self) -> Self:
        """Open the connection, calling the `connect` method."""
        try:
            await self.connect()
        except:  # context manager should always cleanup, but __exit__ wont be called
            # because we did not enter successfully
            await self.disconnect()
            raise
        return self

    async def __aexit__(self, *args) -> None:
        """Close the connection, calling the `disconnect` method."""
        await self.disconnect()

    async def _set_connection_state(self, state: "ConnectionStateType") -> None:
        self._connection_state = state

    @property
    def connection_state(self) -> "ConnectionStateType":
        """Return enum for the current connection state."""
        return self._connection_state

    async def _set_connection_last_used(
        self, last_used: datetime.datetime | None = None
    ) -> None:
        """Set the last contact time for the connection.

        This should be called anytime a connection is used to minimize unnecessary polling
        is using the `keepalive` method.

        Args:
            last_used: Optional. If not given, defaults to current datetime. This datetime
                must be timezone aware.
        """
        self._connection_last_used = last_used or datetime.datetime.now().astimezone()

    @property
    def connection_last_used(self) -> datetime.datetime | None:
        """Return last datetime when communication was made successfully using this connection."""
        return self._connection_last_used

    @abstractmethod
    async def connect(self) -> None:
        """Attempt a connection to/for the object, which can be cancelled
        if it takes too long."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect for/from the object. Cannot be cancelled."""

    @abstractmethod
    async def poll(self) -> bool:
        """Poll to check the connection status, returning True for
        connected and False for disconnected."""

    async def keepalive(self) -> None:
        """Keep the connection alive by polling, but only when in a CONNECTED state and only when
        the connection has not been used in a while.

        Default implementation checks the connection state first and if not CONNECTED, it is a no-op.
        If CONNECTED, it checks the `connection_last_used` property and only polls
        if the value is None or if last contact was made more than `connection_keepalive_timeout`
        ago from current time.

        This allows for `smart polling` that reduces unnecessary IO when we already have
        recent communication which confirms the connection state and reduces chance of background
        keepalive tasks from potentially interrupting ongoing communications in another thread/task.
        """
        if self.connection_state != ConnectionStateType.CONNECTED:
            return
        if self.connection_keepalive_timeout is None:
            raise RuntimeError(
                "connection_keepalive_timeout set to None, but must be set to datetime.timedelta."
            )
        last_used = self.connection_last_used
        if (
            last_used is not None
            and (datetime.datetime.now().astimezone() - last_used)
            < self.connection_keepalive_timeout
        ):
            return
        await self.poll()
