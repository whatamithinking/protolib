from abc import ABC, abstractmethod
from typing import *
import functools
from enum import Enum
import inspect
import functools

from .util import leaf_method

__all__ = [
    "OpenStateType",
    "OpenStateError",
    "NotOpenError",
    "NotClosedError",
    "ClosedError",
    "check_open",
    "ensure_open",
    "check_closed",
    "ensure_closed",
    "check_not_closed",
    "ensure_not_closed",
    "opener",
    "closer",
    "Openable",
    "AsyncOpenable",
]


T = TypeVar("T")
P = ParamSpec("P")


class OpenStateType(str, Enum):
    ERROR = "error"
    OPENING = "opening"
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"


class OpenStateError(Exception):
    """Raised when object not in one of several allowed states."""


class NotOpenError(OpenStateError):
    """Raised when attempt made to call method when object
    not in an open state."""


class NotClosedError(OpenStateError):
    """Raised when attempt made to open an object when it
    is not currently in a closed state."""


class ClosedError(OpenStateError):
    """Raised when attempt made to use an object which is in a closed state."""


def check_open(obj: Union["AsyncOpenable", "Openable"]) -> None:
    """Check if the given object is open and raise an exception, NotOpenError,
    if not."""
    if not isinstance(obj, (AsyncOpenable, Openable)):
        raise TypeError(f"AsyncOpenable or Openable expected, but {type(obj)} given.")
    if obj.open_state != OpenStateType.OPEN:
        raise NotOpenError(
            f"Cannot perform the operation while not "
            + f"in {OpenStateType.OPEN} state."
        )


def ensure_open(method: Callable[P, T]) -> Callable[P, T]:
    """Decorator to check if the method's object is open and raise an exception,
    NotOpenError, if not."""
    if inspect.iscoroutinefunction(method):

        @functools.wraps(method)
        async def _ensure_open(self, *args: P.args, **kwargs: P.kwargs) -> T:
            check_open(self)
            return await method(self, *args, **kwargs)

    elif inspect.isasyncgenfunction(method):

        @functools.wraps(method)
        async def _ensure_open(
            self, *args: P.args, **kwargs: P.kwargs
        ) -> AsyncIterator[T]:
            check_open(self)
            async for _ in method(self, *args, **kwargs):
                yield _

    elif inspect.isgeneratorfunction(method):

        @functools.wraps(method)
        def _ensure_open(self, *args: P.args, **kwargs: P.kwargs) -> Iterator[T]:
            check_open(self)
            yield from method(self, *args, **kwargs)

    else:

        @functools.wraps(method)
        def _ensure_open(self, *args: P.args, **kwargs: P.kwargs) -> T:
            check_open(self)
            return method(self, *args, **kwargs)

    return _ensure_open


def check_closed(obj: Union["AsyncOpenable", "Openable"]) -> None:
    """Check if the given object is closed and raise an exception, NotClosedError,
    if not."""
    if not isinstance(obj, (AsyncOpenable, Openable)):
        raise TypeError(f"AsyncOpenable or Openable expected, but {type(obj)} given.")
    if obj.open_state != OpenStateType.CLOSED:
        raise NotClosedError(
            f"Cannot perform the operation while not "
            + f"in {OpenStateType.CLOSED} state."
        )


def ensure_closed(method: Callable[P, T]) -> Callable[P, T]:
    """Decorator to check if the method's object is closed and raise an exception,
    NotClosedError, if not."""
    if inspect.iscoroutinefunction(method):

        @functools.wraps(method)
        async def _ensure_closed(self, *args: P.args, **kwargs: P.kwargs) -> T:
            check_closed(self)
            return await method(self, *args, **kwargs)

    elif inspect.isasyncgenfunction(method):

        @functools.wraps(method)
        async def _ensure_closed(
            self, *args: P.args, **kwargs: P.kwargs
        ) -> AsyncIterator[T]:
            check_closed(self)
            async for _ in method(self, *args, **kwargs):
                yield _

    elif inspect.isgeneratorfunction(method):

        @functools.wraps(method)
        def _ensure_closed(self, *args: P.args, **kwargs: P.kwargs) -> Iterator[T]:
            check_closed(self)
            yield from method(self, *args, **kwargs)

    else:

        @functools.wraps(method)
        def _ensure_closed(self, *args: P.args, **kwargs: P.kwargs) -> T:
            check_closed(self)
            return method(self, *args, **kwargs)

    return _ensure_closed


def check_not_closed(obj: Union["AsyncOpenable", "Openable"]) -> None:
    """Check if the given object is not closed and raise an exception, ClosedError,
    if not."""
    if not isinstance(obj, (AsyncOpenable, Openable)):
        raise TypeError(f"AsyncOpenable or Openable expected, but {type(obj)} given.")
    if obj.open_state == OpenStateType.CLOSED:
        raise ClosedError(
            f"Cannot perform the operation while in {OpenStateType.CLOSED} state."
        )


def ensure_not_closed(method: Callable[P, T]) -> Callable[P, T]:
    """Decorator to check if the method's object is not closed and raise an exception,
    ClosedError, if not."""
    if inspect.iscoroutinefunction(method):

        @functools.wraps(method)
        async def _ensure_not_closed(self, *args: P.args, **kwargs: P.kwargs) -> T:
            check_not_closed(self)
            return await method(self, *args, **kwargs)

    elif inspect.isasyncgenfunction(method):

        @functools.wraps(method)
        async def _ensure_not_closed(
            self, *args: P.args, **kwargs: P.kwargs
        ) -> AsyncIterator[T]:
            check_not_closed(self)
            async for _ in method(self, *args, **kwargs):
                yield _

    elif inspect.isgeneratorfunction(method):

        @functools.wraps(method)
        def _ensure_not_closed(self, *args: P.args, **kwargs: P.kwargs) -> Iterator[T]:
            check_not_closed(self)
            yield from method(self, *args, **kwargs)

    else:

        @functools.wraps(method)
        def _ensure_not_closed(self, *args: P.args, **kwargs: P.kwargs) -> T:
            check_not_closed(self)
            return method(self, *args, **kwargs)

    return _ensure_not_closed


@leaf_method
def opener(method: Callable[P, T]) -> T:
    """Decorator for open method to handle state changes.

    This decorator will prevent the decorated method from being
    called unless in a closed state to ensure resources are cleaned
    up before attempting to open again.

    If already open, a call to a method using this decorator will
    return without running.
    The decorator will only run on the childmost method in a
    subclass call chain.
    """
    if inspect.iscoroutinefunction(method):

        @functools.wraps(method)
        async def _opener(self, *args: P.args, **kwargs: P.kwargs) -> T:
            if not isinstance(self, AsyncOpenable):
                raise TypeError(f"AsyncOpenable expected, but {type(self)} given.")
            if self.open_state == OpenStateType.OPEN:
                return
            check_closed(self)
            await self._set_open_state(OpenStateType.OPENING)
            try:
                result = await method(self, *args, **kwargs)
            except:
                await self._set_open_state(OpenStateType.ERROR)
                raise
            else:
                await self._set_open_state(OpenStateType.OPEN)
                return result

    else:

        @functools.wraps(method)
        def _opener(self, *args: P.args, **kwargs: P.kwargs) -> T:
            if not isinstance(self, Openable):
                raise TypeError(f"Openable expected, but {type(self)} given.")
            if self.open_state == OpenStateType.OPEN:
                return
            check_closed(self)
            self._set_open_state(OpenStateType.OPENING)
            try:
                result = method(self, *args, **kwargs)
            except:
                self._set_open_state(OpenStateType.ERROR)
                raise
            else:
                self._set_open_state(OpenStateType.OPEN)
                return result

    return _opener


@leaf_method
def closer(method: Callable[P, T]) -> T:
    """Decorator for close method to handle state changes.

    If already closed, a call to a method using this decorator will
    return without running.
    The decorator will only run on the childmost method in a
    subclass call chain.
    """
    if inspect.iscoroutinefunction(method):

        @functools.wraps(method)
        async def _closer(self, *args: P.args, **kwargs: P.kwargs) -> T:
            if not isinstance(self, AsyncOpenable):
                raise TypeError(f"AsyncOpenable expected, but {type(self)} given.")
            if self.open_state == OpenStateType.CLOSED:
                return
            await self._set_open_state(OpenStateType.CLOSING)
            try:
                result = await method(self, *args, **kwargs)
            except:
                await self._set_open_state(OpenStateType.ERROR)
                raise
            else:
                await self._set_open_state(OpenStateType.CLOSED)
                return result

    else:

        @functools.wraps(method)
        def _closer(self, *args: P.args, **kwargs: P.kwargs) -> T:
            if not isinstance(self, Openable):
                raise TypeError(f"Openable expected, but {type(self)} given.")
            if self.open_state == OpenStateType.CLOSED:
                return
            self._set_open_state(OpenStateType.CLOSING)
            try:
                result = method(self, *args, **kwargs)
            except:
                self._set_open_state(OpenStateType.ERROR)
                raise
            else:
                self._set_open_state(OpenStateType.CLOSED)
                return result

    return _closer


class Openable(ABC):
    """Sync Open/Close interface and state control.

    Open/Close can be used as standard setup/teardown methods for handling
    expensive resources used by an object.
    """

    _open_state: OpenStateType = OpenStateType.CLOSED

    def _set_open_state(self, state: "OpenStateType") -> None:
        self._open_state = state

    @property
    def open_state(self) -> OpenStateType:
        """Return an enum for the current open state of the object."""
        return self._open_state

    @abstractmethod
    def open(self, timeout: Optional[float] = None) -> None:
        """Open up the object, allocating expensive or one-time resources.
        Cannot be cancelled."""

    @abstractmethod
    def close(self, timeout: Optional[float] = None) -> None:
        """Close the object, cleaning up any/all resources. Cannot be cancelled.

        This should never fail/raise an exception.
        """

    def __enter__(self) -> Self:
        """Open up the object, calling the `open` method."""
        try:
            self.open()
        except:  # context manager should always cleanup, but __exit__ wont be called
            # because we did not enter successfully
            self.close()
            raise
        return self

    def __exit__(self, *args) -> None:
        """Close the object, calling the `close` method."""
        self.close()


class AsyncOpenable(ABC):
    """Async Open/Close interface and state control.

    Open/Close can be used as standard setup/teardown methods for handling
    expensive resources used by an object.
    """

    _open_state: OpenStateType = OpenStateType.CLOSED

    async def _set_open_state(self, state: "OpenStateType") -> None:
        self._open_state = state

    @property
    def open_state(self) -> OpenStateType:
        """Return an enum for the current open state of the object."""
        return self._open_state

    @abstractmethod
    async def open(self) -> None:
        """Open up the object, allocating expensive or one-time resources.
        Cannot be cancelled."""

    @abstractmethod
    async def close(self) -> None:
        """Close the object, cleaning up any/all resources. Cannot be cancelled.

        This should never fail/raise an exception.
        """

    async def __aenter__(self) -> Self:
        """Open up the object, calling the `open` method."""
        try:
            await self.open()
        except:  # context manager should always cleanup, but __aexit__ wont be called
            # because we did not enter successfully
            await self.close()
            raise
        return self

    async def __aexit__(self, *args) -> None:
        """Close the object, calling the `close` method."""
        await self.close()
