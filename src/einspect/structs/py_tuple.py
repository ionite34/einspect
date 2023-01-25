from __future__ import annotations

import ctypes
from collections.abc import Sequence
from ctypes import POINTER, pointer, pythonapi, sizeof
from typing import Any, TypeVar, overload

from einspect.api import Py_ssize_t, seq_to_array
from einspect.protocols.delayed_bind import bind_api
from einspect.structs.deco import struct
from einspect.structs.py_object import Fields, PyObject, PyVarObject
from einspect.structs.traits import IsGC
from einspect.types import Array, ptr

_VT = TypeVar("_VT")


@struct
class PyTupleObject(PyVarObject[tuple, None, _VT], IsGC):
    """
    Defines a PyTupleObject Structure.

    https://github.com/python/cpython/blob/3.11/Include/cpython/tupleobject.h
    """

    # Size of this array is only known after creation
    # this field just serves to get the address of the array
    _ob_item_0: ptr[PyObject] * 0

    def _format_fields_(self) -> Fields:
        return {**super()._format_fields_(), "ob_item": "Array[*PyObject]"}

    @overload
    @classmethod
    def from_object(cls, obj: tuple[_VT, ...]) -> PyTupleObject[_VT]:
        ...

    @overload
    @classmethod
    def from_object(cls, obj: tuple[...]) -> PyTupleObject[Any]:
        ...

    @classmethod
    def from_object(cls, obj: tuple[_VT, ...]) -> PyTupleObject[_VT]:
        """Create a PyTupleObject from an object."""
        return super().from_object(obj)  # type: ignore

    @property
    def mem_size(self) -> int:
        """Return the size of the PyObject in memory."""
        # Need to add size * ob_size to our base size
        base = super().mem_size
        int_size = ctypes.sizeof(Py_ssize_t)
        return base + (int_size * self.ob_size)

    @property
    def ob_item(self) -> Array[ptr[PyObject]]:
        """Return the ob_item field."""
        items_addr = ctypes.addressof(self._ob_item_0)
        arr = POINTER(PyObject) * self.ob_size
        return arr.from_address(items_addr)

    @ob_item.setter
    def ob_item(self, value: Array[ptr[PyObject]] | Sequence[ptr[PyObject]]) -> None:
        """Set the ob_item field."""
        arr = seq_to_array(value, ptr[PyObject])
        items_addr = ctypes.addressof(self._ob_item_0)
        ctypes.memmove(items_addr, arr, sizeof(arr))

    @bind_api(pythonapi["PyTuple_GetItem"])
    def GetItem(self, index: int) -> pointer[PyObject[_VT, None, None]]:
        """Return the item at the given index."""

    @bind_api(pythonapi["PyTuple_GetSlice"])
    def GetSlice(self, start: int, stop: int) -> pointer[PyTupleObject[_VT]]:
        """Return a slice of the tuple."""

    @bind_api(pythonapi["PyTuple_SetItem"])
    def SetItem(self, index: int, value: object) -> int:
        """
        Set a value to a given index.

        - Can only be used when refcount is equal to 1.
        """

    @bind_api(pythonapi["_PyTuple_Resize"])
    def Resize(self, size: int) -> None:
        """Resize the tuple to the given size."""
