"""Traits and mixins for structs."""
from ctypes import Structure, addressof, pointer

from typing_extensions import Self

from einspect.types import ptr


class AsRef:
    """Mixin for an as_ref method."""

    def as_ref(self) -> ptr[Self]:
        """Return a pointer to the Structure."""
        return pointer(self)  # type: ignore


class Display:
    """Mixin for displaying Structures."""

    def __repr__(self: Structure) -> str:
        """
        Return a string representation of the Structure.
        The address shown is the address of the Structure, not the object.
        """
        return f"<{self.__class__.__name__} at {addressof(self):#04x}>"


class IsGC:
    """Mixin for Structures that have a GC_Head."""

    _is_gc_ = True
