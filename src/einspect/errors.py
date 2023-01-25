from __future__ import annotations


class MovedError(ReferenceError):
    """Unreachable weak referenced object."""


class UnsafeError(RuntimeError):
    """Unsafe operation without unsafe context."""


class DroppedReferenceError(RuntimeError):
    """Raised on access to a dropped object's reference."""


class DroppedReference:
    """Dropped reference to an object."""

    __slots__ = ("__parent_cls",)

    def __init__(self, parent_cls: type) -> None:
        """Initialize the dropped reference."""
        self.__parent_cls = parent_cls

    def __getattr__(self, item):
        raise DroppedReferenceError(
            f"Reference to {self.__parent_cls.__name__!r} has been dropped, "
            "cannot access attributes."
        ) from None
