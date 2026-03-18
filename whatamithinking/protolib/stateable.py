import threading
from abc import ABC
from typing import Optional

from .lockable import Lockable

__all__ = ["Stateable"]


class Stateable(ABC):
    """Base class for sync objects that own state and must notify waiters of state changes.

    Provides a single :attr:`_state_changed` :class:`threading.Condition` that every
    state-owning mixin (``Connectable``, ``Openable``, ``Enableable``, …) shares on the
    same instance.  Because Python provides no mechanism to wait on multiple
    ``Condition`` objects simultaneously, a single shared condition is the only reliable
    way to block until *any* state dimension changes on a composite object.

    Each mixin's ``_set_*_state`` helper acquires ``_state_changed`` before mutating its
    state variable and calls ``notify_all()`` afterward, so a waiter holding the same
    condition is woken regardless of which mixin triggered the change.

    When the concrete class also inherits from :class:`~.lockable.Lockable` the
    ``Condition`` is backed by ``self.lock`` so that the existing re-entrant lock is
    reused as the underlying primitive and all locking is consolidated.  Otherwise a
    fresh ``threading.RLock`` is created internally by :class:`threading.Condition`.
    """

    _state_changed: Optional[threading.Condition] = None

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        if self._state_changed is None:
            self._state_changed = threading.Condition(
                self.lock if isinstance(self, Lockable) else None
            )
