"""Methods for managing unsafe contexts for views."""
from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from functools import wraps
from typing import TYPE_CHECKING, TypeVar

from typing_extensions import ContextManager, ParamSpec, Self

from einspect.errors import UnsafeError

if TYPE_CHECKING:
    from einspect.views.view_base import View

_T = TypeVar("_T")
_P = ParamSpec("_P")


class UnsafeContext:
    _global_unsafe = False

    def __init__(self):
        super().__init__()
        self._local_unsafe = False

    @property
    def _unsafe(self) -> bool:
        """Returns True if unsafe operations are allowed."""
        return self._global_unsafe or self._local_unsafe

    def unsafe(self) -> ContextManager[Self]:
        """
        Context manager to enter an unsafe context.

        Examples:
            >>> from einspect import view
            >>> v = view(100)
            >>> with v.unsafe():
            >>>     v.size += 1

            >>> with view(100).unsafe() as v:
            >>>     v.size -= 1
        """

        def ctx() -> Generator[Self, None, None]:
            self._local_unsafe = True
            try:
                yield self
            finally:
                self._local_unsafe = False

        return contextmanager(ctx)()


@contextmanager
def global_unsafe() -> Generator[None, None, None]:
    """Context manager for global unsafe contexts."""
    UnsafeContext._global_unsafe = True
    yield None
    UnsafeContext._global_unsafe = False


def unsafe(func: _T) -> _T:
    """Decorator for unsafe methods on Views."""

    @wraps(func)
    def unsafe_call(self: View, *args: _P.args, **kwargs: _P.kwargs) -> _T:
        # noinspection PyProtectedMember
        if not self._unsafe:
            raise UnsafeError(f"Call to {func.__qualname__} requires unsafe context")
        return func(self, *args, **kwargs)

    return unsafe_call
