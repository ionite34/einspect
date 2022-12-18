from __future__ import annotations

import ctypes
from ctypes import Array
from typing import Iterable, TypeVar

from einspect.api import Py_ssize_t
from einspect.structs.py_float import PyFloatObject
from einspect.views.unsafe import unsafe
from einspect.views.view_base import View

_T = TypeVar("_T")


class FloatView(View[_T]):
    _pyobject: PyFloatObject

    @property
    def mem_size(self):
        return object.__sizeof__(self.value)

    @property
    def value(self) -> float:
        return self._pyobject.ob_fval  # type: ignore

    @value.setter
    @unsafe
    def value(self, obj: float | ctypes.c_double) -> None:
        self._pyobject.ob_fval = obj
