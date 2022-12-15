from __future__ import annotations

from collections.abc import Sequence
from ctypes import Array
from typing import TypeVar, overload

from einspect.api import Py_ssize_t
from einspect.structs import PyUnicodeObject
from einspect.structs.py_unicode import State
from einspect.views.unsafe import unsafe
from einspect.views.view_base import View

_T = TypeVar("_T")


class StrView(View[_T], Sequence):
    _pyobject: PyUnicodeObject

    @property
    def mem_size(self) -> int:
        return object.__sizeof__(self.base.value)

    @property
    def length(self) -> int:
        return self._pyobject.length

    @length.setter
    def length(self, value: int) -> None:
        self._pyobject.length = value

    @property
    def hash(self) -> int:
        return self._pyobject.hash  # type: ignore

    @hash.setter
    @unsafe
    def hash(self, value: int) -> None:
        self._pyobject.hash = value

    @property
    def interned(self) -> State:
        return self._pyobject.interned

    @interned.setter
    def interned(self, value: State) -> None:
        self._pyobject.interned = value

    @property
    def kind(self) -> int:
        return self._pyobject.kind

    @kind.setter
    def kind(self, value: int) -> None:
        self._pyobject.kind = value

    @property
    def buffer(self) -> Array[Py_ssize_t]:
        return self._pyobject.buffer

    def __len__(self) -> int:
        return str.__len__(self.base.value)

    @overload
    def __getitem__(self, index: int) -> _T: ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[_T]: ...

    def __getitem__(self, index: int | slice) -> _T:
        return str.__getitem__(self.base.value, index)




