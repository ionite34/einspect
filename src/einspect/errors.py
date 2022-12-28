from __future__ import annotations


class MovedError(ReferenceError):
    """Unreachable weak referenced object."""


class UnsafeError(RuntimeError):
    """Unsafe operation without unsafe context."""


class UnsafeAttributeError(UnsafeError, AttributeError):
    """Unsafe attribute access."""

    @classmethod
    def from_attr(cls, attr: str) -> UnsafeError:
        """Create an UnsafeError from an attribute name."""
        return cls(
            f"Setting attribute {attr!r} requires "
            f"entering the unsafe() context manager"
        )


class UnsafeIndexError(UnsafeError, IndexError):
    """Unsafe index access."""


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
