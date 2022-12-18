from __future__ import annotations

import ctypes
from collections.abc import Callable
from ctypes import pythonapi
from types import MethodType
from typing import Generic, TypeVar, get_args, overload

from typing_extensions import Self

from einspect.api import Py_ssize_t
from einspect.protocols import bind_api, delayed_bind
from einspect.structs.deco import struct
from einspect.structs.py_object import PyVarObject

_Tuple = TypeVar("_Tuple", bound=tuple)


# noinspection PyPep8Naming
@struct
class PyTupleObject(PyVarObject[_Tuple]):
    """
    Defines a PyTupleObject Structure.

    https://github.com/python/cpython/blob/3.11/Include/cpython/tupleobject.h
    """
    # Size of this array is only known after creation
    _ob_item_0: Py_ssize_t * 0

    @bind_api(pythonapi["PyTuple_GetItem"])
    def GetItem(self, index: int) -> object:
        """Return the item at the given index."""

    @bind_api(pythonapi["PyTuple_SetItem"])
    def SetItem(self, index: int, value: object) -> None:
        """Set a value to a given index."""

    @bind_api(pythonapi["_PyTuple_Resize"])
    def Resize(self, size: int) -> None:
        """Resize the tuple to the given size."""

    @classmethod
    def from_object(cls, obj: _Tuple) -> PyTupleObject[_Tuple]:
        """Create a PyTupleObject from an object."""
        return super(PyTupleObject, cls).from_object(obj)  # type: ignore

    @property
    def mem_size(self) -> int:
        """Return the size of the PyObject in memory."""
        # Need to add size * ob_size to our base size
        base = super().mem_size
        int_size = ctypes.sizeof(Py_ssize_t)
        return base + (int_size * self.ob_size)

    @property
    def ob_item(self):
        items_addr = ctypes.addressof(self._ob_item_0)
        arr = Py_ssize_t * self.ob_size
        return arr.from_address(items_addr)
