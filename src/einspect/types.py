import ctypes
import typing
from ctypes import pointer as ptr
# noinspection PyUnresolvedReferences, PyProtectedMember
from ctypes import _Pointer
from typing import TypeVar, TYPE_CHECKING, get_origin, overload

__all__ = ("ptr", "Array")

_T = TypeVar("_T")


# noinspection PyPep8Naming
class _Ptr(_Pointer):
    def __new__(cls, *args, **kwargs):
        return ctypes.pointer(*args, **kwargs)

    def __class_getitem__(cls, item):
        # Get base of generic alias
        # noinspection PyUnresolvedReferences, PyProtectedMember
        if isinstance(item, typing._GenericAlias):
            item = get_origin(item)

        return ctypes.POINTER(item)


class Array(ctypes.Array[_T]):
    _length_ = 0
    _type_ = ctypes.c_void_p

    @overload
    def __getitem__(self, item: int) -> _T:
        ...

    @overload
    def __getitem__(self, item: slice) -> list[_T]:
        ...

    def __getitem__(self, item):
        raise NotImplementedError


if not TYPE_CHECKING:
    globals().update({
        "ptr": _Ptr,
        "Array": ctypes.Array,
    })
