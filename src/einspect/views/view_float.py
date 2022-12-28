from __future__ import annotations

import ctypes
from typing import TypeVar

from einspect.structs.py_float import PyFloatObject
from einspect.views.unsafe import unsafe
from einspect.views.view_base import View

__all__ = ("FloatView",)

_T = TypeVar("_T")


class FloatView(View[float, None, None]):
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
