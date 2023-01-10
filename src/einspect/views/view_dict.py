from __future__ import annotations

from ctypes import Array
from typing import TypeVar

from einspect.api import Py_ssize_t
from einspect.compat import abc
from einspect.structs.py_dict import PyDictObject
from einspect.views.unsafe import unsafe
from einspect.views.view_base import REF_DEFAULT, View

__all__ = ("DictView",)

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class DictView(View[dict, _KT, _VT], abc.MutableMapping[_KT, _VT]):
    _pyobject: PyDictObject[_KT, _VT]

    def __init__(self, obj: dict[_KT, _VT], ref: bool = REF_DEFAULT) -> None:
        super().__init__(obj, ref)

    def __len__(self) -> int:
        return self.used

    def __iter__(self) -> abc.Iterator[_KT]:
        ...

    def __getitem__(self, key: _KT) -> _VT:
        return self._pyobject.GetItem(key)

    def __setitem__(self, key: _KT, value: _VT) -> None:
        if self._pyobject.SetItem(key, value) < 0:
            raise RuntimeError("Failed to set item")
        return None

    def __delitem__(self, key: _KT) -> None:
        ...

    @property
    def used(self) -> int:
        return self._pyobject.ma_used  # type: ignore

    @used.setter
    @unsafe
    def used(self, value: int) -> None:
        self._pyobject.ma_used = value

    @property
    def version_tag(self) -> int:
        return self._pyobject.ma_version_tag  # type: ignore

    @version_tag.setter
    @unsafe
    def version_tag(self, value: int) -> None:
        self._pyobject.ma_version_tag = value

    @property
    def ma_keys(self) -> Array[Py_ssize_t]:
        return self._pyobject.ma_keys  # type: ignore

    @ma_keys.setter
    @unsafe
    def ma_keys(self, value: Array[Py_ssize_t]) -> None:
        self._pyobject.ma_keys = value

    @property
    def ma_values(self) -> Array[Py_ssize_t]:
        return self._pyobject.ma_values  # type: ignore

    @ma_values.setter
    @unsafe
    def ma_values(self, value: Array[Py_ssize_t]) -> None:
        self._pyobject.ma_values = value
