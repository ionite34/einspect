"""Runtime patches."""
from __future__ import annotations

import ctypes
from ctypes import POINTER, addressof, c_void_p, memmove, sizeof

from einspect import types
from einspect.structs.py_object import PyObject
from einspect.types import Pointer, PyCFuncPtrType


class _Null_LP_PyObject(POINTER(PyObject)):
    _type_ = PyObject

    def __repr__(self) -> str:
        """Returns the string representation of the pointer."""
        return f"<Null LP_PyObject at {addressof(self):#04x}>"

    def __eq__(self, other) -> bool:
        """Returns equal to other null pointers."""
        if isinstance(other, Pointer):
            return not other

        if isinstance(type(other), PyCFuncPtrType):
            return not ctypes.cast(other, c_void_p)

        return NotImplemented


def run() -> None:
    new_null = _Null_LP_PyObject()
    PyObject.from_object(new_null).IncRef()

    # Move the instance dict
    types.NULL.__dict__ = new_null.__dict__

    # Move the pointer object (excluding ob_refcnt)
    ptr_size = sizeof(c_void_p)
    memmove(
        id(types.NULL) + ptr_size,
        id(new_null) + ptr_size,
        types.NULL.__sizeof__() - ptr_size,
    )
