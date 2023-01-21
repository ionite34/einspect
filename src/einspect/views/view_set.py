from __future__ import annotations

from ctypes import POINTER, cast
from typing import TypeVar

from einspect.structs import PyObject
from einspect.structs.py_set import PySetObject, SetEntry
from einspect.types import Array, ptr
from einspect.views.unsafe import unsafe
from einspect.views.view_base import REF_DEFAULT, View

__all__ = ("SetView",)

_T = TypeVar("_T")


class SetView(View[set, None, _T]):
    _pyobject: PySetObject[_T]

    def __init__(self, obj: set[_T], ref: bool = REF_DEFAULT) -> None:
        super().__init__(obj, ref)

    def __len__(self) -> int:
        return self.used

    @property
    def fill(self) -> int:
        """Number active and dummy entries."""
        return self._pyobject.fill

    @fill.setter
    @unsafe
    def fill(self, value: int) -> None:
        """Number active and dummy entries."""
        self._pyobject.fill = value

    @property
    def used(self) -> int:
        return self._pyobject.used

    @used.setter
    @unsafe
    def used(self, value: int) -> None:
        self._pyobject.used = value

    @property
    def mask(self) -> int:
        return self._pyobject.mask

    @mask.setter
    @unsafe
    def mask(self, value: int) -> None:
        self._pyobject.mask = value

    @property
    def table(self) -> Array[SetEntry[_T]]:
        size = self.mask + 1
        arr = cast(self._pyobject.table, POINTER(SetEntry * size))
        return arr.contents

    @table.setter
    @unsafe
    def table(self, value: Array[SetEntry[_T]]) -> None:
        self._pyobject.table = ptr(value[0])

    @property
    def finger(self) -> int:
        """Search finger for pop()"""
        return self._pyobject.finger

    @finger.setter
    @unsafe
    def finger(self, value: int) -> None:
        """Set search finger for pop()"""
        self._pyobject.finger = value

    @property
    def smalltable(self) -> Array[SetEntry[_T]]:
        return self._pyobject.smalltable

    @smalltable.setter
    @unsafe
    def smalltable(self, value: Array[SetEntry[_T]]) -> None:
        self._pyobject.smalltable = value

    @property
    def weakreflist(self) -> ptr[PyObject]:
        return self._pyobject.weakreflist

    @weakreflist.setter
    @unsafe
    def weakreflist(self, value: ptr[PyObject]) -> None:
        self._pyobject.weakreflist = value
