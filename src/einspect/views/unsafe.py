"""Methods for managing unsafe contexts for views."""
from __future__ import annotations

from collections.abc import Generator
from contextlib import ExitStack, contextmanager
from functools import wraps
from typing import TYPE_CHECKING, Callable, ContextManager

from einspect.errors import UnsafeError

if TYPE_CHECKING:
    from einspect.views.view_base import View


class Context:
    _global_unsafe = False

    def __enter__(self):
        Context._global_unsafe = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        Context._global_unsafe = False

    @classmethod
    @contextmanager
    def unsafe(cls, *views: View) -> Generator[None, None, None]:
        """Context manager for unsafe contexts."""
        with ExitStack() as stack:
            # If views, set unsafe on all views
            if views:
                for view in views:
                    if not isinstance(view, View):
                        raise TypeError(f"Expected View, got {type(view)}")
                    ctx: ContextManager[View] = view.unsafe()  # type: ignore
                    stack.enter_context(ctx)
                yield
            else:
                # Otherwise, set global unsafe
                stack.enter_context(cls())
                yield


def unsafe(func: Callable) -> Callable:
    """Decorator for unsafe methods on Views."""

    @wraps(func)
    def unsafe_call(self: View, *args, **kwargs):
        # noinspection PyProtectedMember
        if not self._unsafe:
            raise UnsafeError(f"Call to {func.__qualname__} requires unsafe context")
        return func(self, *args, **kwargs)

    return unsafe_call
