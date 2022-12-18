"""Typed methods from pythonapi."""
from __future__ import annotations

import ctypes
from collections.abc import Callable
from ctypes import POINTER, py_object, pythonapi
from typing import Union

import _ctypes

from einspect.compat import Version, python_req

__all__ = ("Py", "Py_ssize_t", "PyObj_FromPtr")

Py_ssize_t = ctypes.c_ssize_t
"""Constant for type Py_ssize_t."""

ObjectOrRef = Union[py_object, object]
IntSize = Union[int, Py_ssize_t]
PyObjectPtr = POINTER(py_object)


class Py:
    """Typed methods from pythonapi."""

    IncRef: Callable[[ObjectOrRef], None] = pythonapi["Py_IncRef"]
    """
    Increment the reference count of an object.
    https://docs.python.org/3/c-api/refcounting.html#c.Py_IncRef
    """
    IncRef.argtypes = (py_object,)  # type: ignore
    IncRef.restype = None  # type: ignore

    DecRef: Callable[[ObjectOrRef], None] = pythonapi["Py_DecRef"]
    """
    Create a new strong reference to an object.
    Increments ref-count and returns the object.
    https://docs.python.org/3/c-api/refcounting.html#c.Py_DecRef
    """
    DecRef.argtypes = (py_object,)  # type: ignore
    DecRef.restype = None  # type: ignore

    NewRef: Callable[[ObjectOrRef], None] = python_req(Version.PY_3_10) or pythonapi["Py_NewRef"]
    """
    Create a new strong reference to an object, and increments reference count.
    Returns the object.
    https://docs.python.org/3/c-api/refcounting.html#c.Py_NewRef
    """
    NewRef.argtypes = (py_object,)  # type: ignore
    NewRef.restype = py_object  # type: ignore

    class Tuple:
        Size: Callable[[ObjectOrRef], int] = pythonapi["PyTuple_Size"]
        """
        Return the size of a tuple object.
        https://docs.python.org/3/c-api/tuple.html#c.PyTuple_Size
        """
        Size.argtypes = (py_object,)  # type: ignore
        Size.restype = Py_ssize_t  # type: ignore

        GetItem: Callable[[ObjectOrRef, IntSize], object] = pythonapi["PyTuple_GetItem"]
        """
        Return the item at position index in the tuple o.
        https://docs.python.org/3/c-api/tuple.html#c.PyTuple_GetItem
        """
        GetItem.argtypes = (py_object, Py_ssize_t)  # type: ignore
        GetItem.restype = py_object  # type: ignore

        SetItem: Callable[[ObjectOrRef, IntSize, ObjectOrRef], None] = pythonapi["PyTuple_SetItem"]
        """
        Set the item at position index in the tuple o to v.
        https://docs.python.org/3/c-api/tuple.html#c.PyTuple_SetItem
        
        Notes:
            - This function steals a reference to v.
            - Requires tuple o to have a reference count == 1.
        """
        SetItem.argtypes = (py_object, Py_ssize_t, py_object)  # type: ignore
        SetItem.restype = None  # type: ignore

        Resize: Callable[[PyObjectPtr, IntSize], None] = pythonapi["_PyTuple_Resize"]
        """
        Resize the tuple to the specified size.
        https://docs.python.org/3/c-api/tuple.html#c._PyTuple_Resize

        Notes:
            - Not part of the documented limited C API.
            - Requires tuple o to have ref-count = 1 or size = 0
        """
        Resize.argtypes = (POINTER(py_object), Py_ssize_t)  # type: ignore
        Resize.restype = None  # type: ignore

    class Type:
        Modified: Callable[[ObjectOrRef], None] = pythonapi["PyType_Modified"]
        """
        Invalidate the internal lookup cache for the type and all of its subtypes.
        
        - This function must be called after any manual modification of the attributes 
          or base classes of the type.
        """
        Modified.argtypes = (py_object,)  # type: ignore
        Modified.restype = None  # type: ignore


PyObj_FromPtr: Callable[[IntSize], object] = _ctypes.PyObj_FromPtr
"""(Py_ssize_t ptr) -> Py_ssize_t"""
