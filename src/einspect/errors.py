from __future__ import annotations


class MovedError(ReferenceError):
    """Unreachable weak referenced object due to Garbage Collection."""


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
