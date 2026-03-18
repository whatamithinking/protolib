from typing import *
import threading
import functools
from abc import ABC
import inspect

import whatamithinking.aiotools as aiotools

from .util import leaf_method

__all__ = [
    "locked",
    "Lockable",
    "AsyncLockable",
]


T = TypeVar("T")
P = ParamSpec("P")


@leaf_method
def locked(method: Callable[P, T]) -> Callable[P, T]:
    """Method decorator to acquire a lock on an object and hold
    it while calling a method."""
    if inspect.iscoroutinefunction(method):

        @functools.wraps(method)
        async def _locked(self, *args: P.args, **kwargs: P.kwargs) -> T:
            if not isinstance(self, AsyncLockable):
                raise TypeError(f"AsyncLockable expected, but {type(self)} given.")
            async with self.lock:
                return await method(self, *args, **kwargs)

    elif inspect.isasyncgenfunction(method):

        @functools.wraps(method)
        async def _locked(self, *args: P.args, **kwargs: P.kwargs) -> AsyncIterator[T]:
            if not isinstance(self, AsyncLockable):
                raise TypeError(f"AsyncLockable expected, but {type(self)} given.")
            async with self.lock:
                async for _ in method(self, *args, **kwargs):
                    yield _

    elif inspect.isgeneratorfunction(method):

        @functools.wraps(method)
        def _locked(self, *args: P.args, **kwargs: P.kwargs) -> Iterator[T]:
            if not isinstance(self, Lockable):
                raise TypeError(f"Lockable expected, but {type(self)} given.")
            with self.lock:
                yield from method(self, *args, **kwargs)

    else:

        @functools.wraps(method)
        def _locked(self, *args: P.args, **kwargs: P.kwargs) -> T:
            if not isinstance(self, Lockable):
                raise TypeError(f"Lockable expected, but {type(self)} given.")
            with self.lock:
                return method(self, *args, **kwargs)

    return _locked


class Lockable(ABC):
    """Sync lock interface."""

    def __init__(self, lock: Optional[threading.RLock] = None, **kwargs) -> None:
        """Init

        Args:
                lock: Optional. A threading.RLock instance to use. Defaults to
                        creating one internally.
        """
        self.lock = lock or threading.RLock()
        super().__init__(**kwargs)


class AsyncLockable(ABC):
    """Async lock interface."""

    def __init__(self, lock: Optional[aiotools.Lock] = None, **kwargs) -> None:
        """Init

        Args:
                lock: Optional. A `aiotools.Lock` instance to use. Defaults to
                        an `aiotools.RLock` instance which can be re-entered multiple times.
        """
        self.lock = lock or aiotools.RLock()
        super().__init__(**kwargs)
