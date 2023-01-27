from __future__ import annotations

from ctypes import POINTER, c_long, pythonapi
from typing import List, TypeVar

from typing_extensions import Annotated

from einspect.protocols.delayed_bind import bind_api
from einspect.structs.deco import struct
from einspect.structs.py_object import Fields, PyObject, PyVarObject
from einspect.structs.traits import IsGC
from einspect.types import ptr

_VT = TypeVar("_VT")


# noinspection PyPep8Naming
@struct
class PyListObject(PyVarObject[list, None, _VT], IsGC):
    """
    Defines a PyListObject Structure.

    https://github.com/python/cpython/blob/3.11/Include/cpython/listobject.h
    """

    ob_item: ptr[ptr[PyObject[_VT, None, None]]]
    allocated: Annotated[int, c_long]

    @classmethod
    def from_object(cls, obj: list[_VT]) -> PyListObject[_VT]:
        return super().from_object(obj)  # type: ignore

    def _format_fields_(self) -> Fields:
        return {
            **super()._format_fields_(),
            "ob_item": ("**PyObject", ptr[ptr[PyObject] * self.ob_size]),
            "allocated": "c_long",
        }

    @bind_api(pythonapi["PyList_GetItem"])
    def GetItem(self, index: int) -> POINTER(PyObject):
        """
        Return the object at position index in the list pointed to by list.

        - If index is out of bounds (<0 or >=len(list)), return NULL and set an IndexError exception.
        - The position must be non-negative; indexing from the end of the list is not supported.

        Returns:
            pointer[PyObject] (borrowed reference) or pointer[NULL] on failure.
        """

    @bind_api(pythonapi["PyList_GetSlice"])
    def GetSlice(self, low: int, high: int) -> POINTER(PyListObject):
        """
        Return a list of the objects in list containing the objects between low and high.
        Analogous to list[low:high].

        - Return NULL and set an exception if unsuccessful.
        - Indexing from the end of the list is not supported.

        Returns:
            pointer[PyListObject] (new reference) or pointer[NULL] on failure.
        """

    @bind_api(pythonapi["PyList_SetItem"])
    def SetItem(self, index: int, value: object) -> None:
        """Set a value to a given index."""

    @bind_api(pythonapi["PyList_SetSlice"])
    def SetSlice(self, low: int, high: int, item_list: List[_VT]) -> None:
        """Set a value to a given index."""
