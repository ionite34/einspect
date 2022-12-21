from __future__ import annotations

from ctypes import POINTER, c_long, c_void_p, pythonapi
from typing import TypeVar

from einspect.protocols.delayed_bind import bind_api
from einspect.structs.deco import struct
from einspect.structs.py_object import PyObject, PyVarObject

_T = TypeVar("_T", bound=list)


# noinspection PyPep8Naming
@struct
class PyListObject(PyVarObject[_T]):
    """
    Defines a PyListObject Structure.

    https://github.com/python/cpython/blob/3.11/Include/cpython/listobject.h
    """

    ob_item: POINTER(c_void_p)
    allocated: c_long

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
    def SetSlice(self, low: int, high: int, item_list: _T) -> None:
        """Set a value to a given index."""
