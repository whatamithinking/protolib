import functools
from typing import *
import inspect

__all__ = [
    "leaf_method",
]


T = TypeVar("T")
P = ParamSpec("P")


def leaf_method(dec: T) -> T:
    """Method decorator on a class, so only the
    leaf/child-most subclass method decorator is called.

    Works with multiple decorators on the same object method and with
    duplicate decorator names.
    """

    def leaf_outer(method: Callable[P, T]) -> Callable[P, T]:
        dec_method = dec(method)
        running_attr_name = f"_running_{id(dec)}_{method.__name__}"
        if inspect.iscoroutinefunction(method):

            @functools.wraps(method)
            async def leaf_inner(self, *args: P.args, **kwargs: P.kwargs) -> T:
                if not hasattr(self, running_attr_name):
                    setattr(self, running_attr_name, False)
                try:
                    is_setter = False
                    if not getattr(self, running_attr_name, False):
                        setattr(self, running_attr_name, True)
                        is_setter = True
                        return await dec_method(self, *args, **kwargs)
                    else:
                        return await method(self, *args, **kwargs)
                finally:
                    if is_setter:
                        setattr(self, running_attr_name, False)

        else:

            @functools.wraps(method)
            def leaf_inner(self, *args: P.args, **kwargs: P.kwargs) -> T:
                if not hasattr(self, running_attr_name):
                    setattr(self, running_attr_name, False)
                try:
                    is_setter = False
                    if not getattr(self, running_attr_name, False):
                        setattr(self, running_attr_name, True)
                        is_setter = True
                        return dec_method(self, *args, **kwargs)
                    else:
                        return method(self, *args, **kwargs)
                finally:
                    if is_setter:
                        setattr(self, running_attr_name, False)

        return leaf_inner

    return leaf_outer
