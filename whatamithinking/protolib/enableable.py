import functools
import inspect
from typing import *
from enum import Enum
from abc import ABC, abstractmethod

from .util import *

__all__ = [
    "EnabledStateType",
    "EnableableError",
    "NotEnabledError",
    "check_enabled",
    "ensure_enabled",
    "enabler",
    "disabler",
    "Enableable",
    "AsyncEnableable",
]


T = TypeVar("T")
P = ParamSpec("P")


class EnabledStateType(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"


class EnableableError(Exception):
    """Raised when object not in one of several allowed states."""


class NotEnabledError(EnableableError):
    """Raised when attempt made to call a method on an object when it
    is not currently in a enabled state."""


def check_enabled(obj: Union["AsyncEnableable", "Enableable"]) -> None:
    """Check if the given object is enabled and raise an exception, NotEnabledError,
    if not."""
    if not isinstance(obj, (AsyncEnableable, Enableable)):
        raise TypeError(
            f"AsyncEnableable or Enableable expected, but {type(obj)} given."
        )
    if obj.enabled_state != EnabledStateType.ENABLED:
        raise NotEnabledError(
            f"Cannot perform the operation while not "
            + f"in {EnabledStateType.ENABLED} state."
        )


def ensure_enabled(method: Callable[P, T]) -> Callable[P, T]:
    """Decorator to check if the method's object is enabled and raise an exception,
    NotEnabledError, if not."""
    if inspect.iscoroutinefunction(method):

        @functools.wraps(method)
        async def _ensure_enabled(self, *args: P.args, **kwargs: P.kwargs) -> T:
            check_enabled(self)
            return await method(self, *args, **kwargs)

    elif inspect.isasyncgenfunction(method):

        @functools.wraps(method)
        async def _ensure_enabled(
            self, *args: P.args, **kwargs: P.kwargs
        ) -> AsyncIterator[T]:
            check_enabled(self)
            async for _ in method(self, *args, **kwargs):
                yield _

    elif inspect.isgeneratorfunction(method):

        @functools.wraps(method)
        def _ensure_enabled(self, *args: P.args, **kwargs: P.kwargs) -> Iterator[T]:
            check_enabled(self)
            yield from method(self, *args, **kwargs)

    else:

        @functools.wraps(method)
        def _ensure_enabled(self, *args: P.args, **kwargs: P.kwargs) -> T:
            check_enabled(self)
            return method(self, *args, **kwargs)

    return _ensure_enabled


@leaf_method
def enabler(method: Callable[P, T]) -> T:
    """Decorator for enable method to handle state changes."""
    if inspect.iscoroutinefunction(method):

        @functools.wraps(method)
        async def _enabler(self, *args: P.args, **kwargs: P.kwargs) -> T:
            if self.enabled_state == EnabledStateType.ENABLED:
                return
            try:
                return await method(self, *args, **kwargs)
            finally:
                await self._set_enabled_state(EnabledStateType.ENABLED)

    else:

        @functools.wraps(method)
        def _enabler(self, *args: P.args, **kwargs: P.kwargs) -> T:
            if self.enabled_state == EnabledStateType.ENABLED:
                return
            try:
                return method(self, *args, **kwargs)
            finally:
                self._set_enabled_state(EnabledStateType.ENABLED)

    return _enabler


@leaf_method
def disabler(method: Callable[P, T]) -> T:
    """Decorator for disable method to handle state changes."""
    if inspect.iscoroutinefunction(method):

        @functools.wraps(method)
        async def _disabler(self, *args: P.args, **kwargs: P.kwargs) -> T:
            if self.enabled_state == EnabledStateType.DISABLED:
                return
            try:
                return await method(self, *args, **kwargs)
            finally:
                await self._set_enabled_state(EnabledStateType.DISABLED)

    else:

        @functools.wraps(method)
        def _disabler(self, *args: P.args, **kwargs: P.kwargs) -> T:
            if self.enabled_state == EnabledStateType.DISABLED:
                return
            try:
                return method(self, *args, **kwargs)
            finally:
                self._set_enabled_state(EnabledStateType.DISABLED)

    return _disabler


class Enableable(ABC):
    """Sync enable/disable object."""

    _enabled_state: EnabledStateType = EnabledStateType.DISABLED

    def __init__(
        self, *, enabled_state: Optional["EnabledStateType"] = None, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self._enabled_state: EnabledStateType = enabled_state

    def _set_enabled_state(self, state: "EnabledStateType") -> None:
        self._enabled_state = state

    @property
    def enabled_state(self) -> "EnabledStateType":
        """Return an enum for the current enabled state of the object."""
        return self._enabled_state

    @abstractmethod
    def enable(self, timeout: Optional[float] = None) -> None: ...

    @abstractmethod
    def disable(self, timeout: Optional[float] = None) -> None: ...


class AsyncEnableable(ABC):
    """Async enable/disable object."""

    _enabled_state: EnabledStateType = EnabledStateType.DISABLED

    def __init__(
        self, *, enabled_state: Optional["EnabledStateType"] = None, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self._enabled_state: EnabledStateType = enabled_state

    async def _set_enabled_state(self, state: "EnabledStateType") -> None:
        self._enabled_state = state

    @property
    def enabled_state(self) -> "EnabledStateType":
        """Return an enum for the current enabled state of the object."""
        return self._enabled_state

    @abstractmethod
    async def enable(self) -> None: ...

    @abstractmethod
    async def disable(self) -> None: ...
