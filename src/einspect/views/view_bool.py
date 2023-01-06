from __future__ import annotations

from ctypes import Array, c_uint32, addressof
from typing import Iterable, TypeVar

from einspect.api import Py_ssize_t
from einspect.structs import PyBoolObject
from einspect.utils import address
from einspect.views.view_int import IntView

__all__ = ("BoolView",)


class BoolView(IntView):
    _pyobject: PyBoolObject

    @property
    def mem_size(self) -> int:
        # If used on the singletons, use their
        addr = addressof(self._pyobject)
        if addr == address(True):
            return True.__sizeof__()
        elif addr == address(False):
            return False.__sizeof__()
        return super().mem_size
