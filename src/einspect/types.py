import ctypes
import typing

# noinspection PyUnresolvedReferences, PyProtectedMember
from ctypes import _Pointer
from typing import TYPE_CHECKING, List, TypeVar, get_origin, overload

__all__ = ("ptr", "Array")

_T = TypeVar("_T")

ptr = ctypes.pointer
"""
Dynamic typing alias for ctypes.pointer.

Resolves to the `_Ptr` class at runtime to allow for generic subscripting.
"""


class _Ptr(_Pointer):
    """
    Runtime alias for `ctypes.pointer` to allow generic subscripting.
    """

    def __new__(cls, *args, **kwargs):
        return ctypes.pointer(*args, **kwargs)

    def __class_getitem__(cls, item):
        # Get base of generic alias
        # noinspection PyUnresolvedReferences, PyProtectedMember
        if isinstance(item, typing._GenericAlias):
            item = get_origin(item)

        try:
            return ctypes.POINTER(item)
        except TypeError as e:
            raise TypeError(f"{e} (During POINTER({item}))") from e


if TYPE_CHECKING:  # pragma: no cover
    # This cannot be defined at runtime since 3.8 does not support
    # ctypes.Array subscripting
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
