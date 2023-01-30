from __future__ import annotations

import ctypes
import typing

# noinspection PyUnresolvedReferences, PyProtectedMember
from ctypes import _Pointer
from typing import TYPE_CHECKING, List, TypeVar, get_origin, overload

from typing_extensions import Self

from einspect.compat import Version

if TYPE_CHECKING:
    from einspect.structs import PyObject

__all__ = ("ptr", "Pointer", "Array", "NULL", "_SelfPtr", "SupportsLessThan")

_T = TypeVar("_T")

ptr = ctypes.pointer
"""
Dynamic typing alias for ctypes.pointer.

Resolves to the `_Ptr` class at runtime to allow for generic subscripting.
"""

# noinspection PyUnresolvedReferences, PyProtectedMember
Pointer = ctypes._Pointer
"""Alias to `ctypes._Pointer`."""

_SelfPtr = object()
"""Singleton object returned on ptr[Self]."""

_Null_Type = type(
    "NullType",
    (ctypes.POINTER(ctypes.c_void_p),),
    {
        "_type_": ctypes.c_void_p,
    },
)

NULL: ptr[PyObject] = _Null_Type()
"""Singleton NULL pointer of type ptr[PyObject]."""


class _Ptr(_Pointer):
    """
    Runtime alias for `ctypes.pointer` to allow generic subscripting.
    """

    def __new__(cls, *args, **kwargs):
        """Alias to `ctypes.pointer(*args, **kwargs)`"""
        return ctypes.pointer(*args, **kwargs)

    def __class_getitem__(cls, item):
        """Return a `ctypes.POINTER` of the given type."""
        # For ptr[Self], return a special object
        if item is Self:
            return _SelfPtr

        # Get base of generic alias
        # noinspection PyUnresolvedReferences, PyProtectedMember
        if isinstance(item, typing._GenericAlias):
            item = get_origin(item)

        try:
            return ctypes.POINTER(item)
        except TypeError as e:
            raise TypeError(f"{e} (During POINTER({item}))") from e


if Version.PY_3_9.above():  # pragma: no cover
    # This cannot be defined in 3.8 as ctypes.Array doesn't support subscripting
    class Array(ctypes.Array[_T]):
        """
        A typing alias for ctypes.Array for non-simple types.

        Resolves to ctypes.Array directly at runtime.
        """

        _length_ = 0
        _type_ = ctypes.c_void_p

        @overload
        def __getitem__(self, item: int) -> _T:
            ...

        @overload
        def __getitem__(self, item: slice) -> List[_T]:
            ...

        def __getitem__(self, item):
            raise NotImplementedError


# subclasses of ctypes types to avoid Structure auto casting
class void_p(ctypes.c_void_p):
    pass


class wchar_p(ctypes.c_wchar_p):
    pass


class char_p(ctypes.c_char_p):
    pass


class SupportsLessThan(typing.Protocol):  # pragma: no cover
    def __lt__(self, other: Self) -> bool:
        ...


if not TYPE_CHECKING:
    # Runtime overrides
    globals().update(
        {
            # Overwrite ctypes.pointer -> _Ptr
            "ptr": _Ptr,
            # Define Array as ctypes.Array
            "Array": ctypes.Array,
        }
    )
