"""Runtime patches."""
from __future__ import annotations

import ctypes
from ctypes import POINTER, addressof, c_void_p, memmove, sizeof

from einspect import types
from einspect.structs.py_object import PyObject


class _Null_LP_PyObject(POINTER(PyObject)):
    _type_ = PyObject

    def __repr__(self) -> str:
        """Returns the string representation of the pointer."""
        return f"<NULL ptr[PyObject] at {addressof(self):#04x}>"

    def __eq__(self, other) -> bool:
        """Returns equal to other null pointers."""
        # noinspection PyUnresolvedReferences
        if not isinstance(other, ctypes._Pointer):
            return NotImplemented
        return not other


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
