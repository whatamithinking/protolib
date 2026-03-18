import functools
import inspect
from typing import *
from enum import Enum
from abc import ABC, abstractmethod

from .util import leaf_method

__all__ = [
    "EnabledStateType",
    "EnableableError",
    "NotEnabledError",
    "NotDisabledError",
    "NotBadEnableError",
    "DisabledError",
    "check_enabled",
    "ensure_enabled",
    "check_not_disabled",
    "ensure_not_disabled",
    "check_bad_enable",
    "ensure_bad_enable",
    "enabler",
    "disabler",
    "Enableable",
    "AsyncEnableable",
]


T = TypeVar("T")
P = ParamSpec("P")


class EnabledStateType(str, Enum):
    ERROR = "error"
    ENABLING = "enabling"
    ENABLED = "enabled"
    DISABLING = "disabling"
    DISABLED = "disabled"


class EnableableError(Exception):
    """Base exception for enable/disable-related issues."""


class NotEnabledError(EnableableError):
    """Raised when attempt made to call a method on an object when it
    is not currently in an ENABLED state."""


class NotDisabledError(EnableableError):
    """Raised when attempt made to enable an object when it
    is not currently in a DISABLED state."""


class NotBadEnableError(EnableableError):
    """Raised when attempt made to call a method on an object when it
    is not currently in a DISABLED or ERROR state."""


class DisabledError(EnableableError):
    """Raised when attempt made to use an object which is disabled."""


def check_enabled(obj: Union["AsyncEnableable", "Enableable"]) -> None:
    """Check if the given object is in ENABLED state and raise an exception, NotEnabledError,
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
    """Decorator to check if the method's object is in ENABLED state and raise an exception,
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


def check_not_disabled(obj: Union["AsyncEnableable", "Enableable"]) -> None:
    """Check if the given object is in DISABLED state and raise an exception, DisabledError,
    if so."""
    if not isinstance(obj, (AsyncEnableable, Enableable)):
        raise TypeError(
            f"AsyncEnableable or Enableable expected, but {type(obj)} given."
        )
    if obj.enabled_state == EnabledStateType.DISABLED:
        raise DisabledError(
            f"Cannot perform operation while in {EnabledStateType.DISABLED} state."
        )


def ensure_not_disabled(method: Callable[P, T]) -> Callable[P, T]:
    """Decorator to check if the object is in DISABLED state and raise an exception,
    DisabledError, if so."""
    if inspect.iscoroutinefunction(method):

        @functools.wraps(method)
        async def _ensure_not_disabled(self, *args: P.args, **kwargs: P.kwargs) -> T:
            check_not_disabled(self)
            return await method(self, *args, **kwargs)

    elif inspect.isasyncgenfunction(method):

        @functools.wraps(method)
        async def _ensure_not_disabled(
            self, *args: P.args, **kwargs: P.kwargs
        ) -> AsyncIterator[T]:
            check_not_disabled(self)
            async for _ in method(self, *args, **kwargs):
                yield _

    elif inspect.isgeneratorfunction(method):

        @functools.wraps(method)
        def _ensure_not_disabled(
            self, *args: P.args, **kwargs: P.kwargs
        ) -> Iterator[T]:
            check_not_disabled(self)
            yield from method(self, *args, **kwargs)

    else:

        @functools.wraps(method)
        def _ensure_not_disabled(self, *args: P.args, **kwargs: P.kwargs) -> T:
            check_not_disabled(self)
            return method(self, *args, **kwargs)

    return _ensure_not_disabled


def check_bad_enable(obj: Union["AsyncEnableable", "Enableable"]) -> None:
    """Check if the given object is in DISABLED or ERROR state
    and raise an exception, NotBadEnableError, if not."""
    if not isinstance(obj, (AsyncEnableable, Enableable)):
        raise TypeError(
            f"AsyncEnableable or Enableable expected, but {type(obj)} given."
        )
    if obj.enabled_state not in (
        EnabledStateType.DISABLED,
        EnabledStateType.ERROR,
    ):
        raise NotBadEnableError(
            f"Cannot perform the operation while not "
            f"in {EnabledStateType.DISABLED} or {EnabledStateType.ERROR} state."
        )


def ensure_bad_enable(method: Callable[P, T]) -> Callable[P, T]:
    """Decorator to check if the object is in DISABLED or ERROR state
    and raise an exception, NotBadEnableError, if not."""
    if inspect.iscoroutinefunction(method):

        @functools.wraps(method)
        async def _ensure_bad_enable(self, *args: P.args, **kwargs: P.kwargs) -> T:
            check_bad_enable(self)
            return await method(self, *args, **kwargs)

    elif inspect.isasyncgenfunction(method):

        @functools.wraps(method)
        async def _ensure_bad_enable(
            self, *args: P.args, **kwargs: P.kwargs
        ) -> AsyncIterator[T]:
            check_bad_enable(self)
            async for _ in method(self, *args, **kwargs):
                yield _

    elif inspect.isgeneratorfunction(method):

        @functools.wraps(method)
        def _ensure_bad_enable(self, *args: P.args, **kwargs: P.kwargs) -> Iterator[T]:
            check_bad_enable(self)
            yield from method(self, *args, **kwargs)

    else:

        @functools.wraps(method)
        def _ensure_bad_enable(self, *args: P.args, **kwargs: P.kwargs) -> T:
            check_bad_enable(self)
            return method(self, *args, **kwargs)

    return _ensure_bad_enable


@leaf_method
def enabler(method: Callable[P, T]) -> T:
    """Decorator for enable method to handle state changes.

    If already in an ENABLED state, a method using this decorator
    returns immediately without running the method.
    """
    if inspect.iscoroutinefunction(method):

        @functools.wraps(method)
        async def _enabler(self, *args: P.args, **kwargs: P.kwargs) -> T:
            if self.enabled_state == EnabledStateType.ENABLED:
                return
            if self.enabled_state != EnabledStateType.DISABLED:
                raise NotDisabledError(
                    "The operation cannot be performed unless "
                    + f"in a {EnabledStateType.DISABLED} state."
                )
            await self._set_enabled_state(EnabledStateType.ENABLING)
            try:
                result = await method(self, *args, **kwargs)
            except:
                await self._set_enabled_state(EnabledStateType.ERROR)
                raise
            else:
                await self._set_enabled_state(EnabledStateType.ENABLED)
                return result

    else:

        @functools.wraps(method)
        def _enabler(self, *args: P.args, **kwargs: P.kwargs) -> T:
            if self.enabled_state == EnabledStateType.ENABLED:
                return
            if self.enabled_state != EnabledStateType.DISABLED:
                raise NotDisabledError(
                    "The operation cannot be performed unless "
                    + f"in a {EnabledStateType.DISABLED} state."
                )
            self._set_enabled_state(EnabledStateType.ENABLING)
            try:
                result = method(self, *args, **kwargs)
            except:
                self._set_enabled_state(EnabledStateType.ERROR)
                raise
            else:
                self._set_enabled_state(EnabledStateType.ENABLED)
                return result

    return _enabler


@leaf_method
def disabler(method: Callable[P, T]) -> T:
    """Decorator for disable method to handle state changes."""
    if inspect.iscoroutinefunction(method):

        @functools.wraps(method)
        async def _disabler(self, *args: P.args, **kwargs: P.kwargs) -> T:
            if self.enabled_state == EnabledStateType.DISABLED:
                return
            await self._set_enabled_state(EnabledStateType.DISABLING)
            try:
                result = await method(self, *args, **kwargs)
            except:
                await self._set_enabled_state(EnabledStateType.ERROR)
                raise
            else:
                await self._set_enabled_state(EnabledStateType.DISABLED)
                return result

    else:

        @functools.wraps(method)
        def _disabler(self, *args: P.args, **kwargs: P.kwargs) -> T:
            if self.enabled_state == EnabledStateType.DISABLED:
                return
            self._set_enabled_state(EnabledStateType.DISABLING)
            try:
                result = method(self, *args, **kwargs)
            except:
                self._set_enabled_state(EnabledStateType.ERROR)
                raise
            else:
                self._set_enabled_state(EnabledStateType.DISABLED)
                return result

    return _disabler


class Enableable(ABC):
    """Sync enable/disable object."""

    _enabled_state: EnabledStateType = EnabledStateType.DISABLED

    def __init__(
        self, *, enabled_state: Optional["EnabledStateType"] = None, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self._enabled_state: EnabledStateType = (
            enabled_state if enabled_state is not None else EnabledStateType.DISABLED
        )

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
        self._enabled_state: EnabledStateType = (
            enabled_state if enabled_state is not None else EnabledStateType.DISABLED
        )

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
