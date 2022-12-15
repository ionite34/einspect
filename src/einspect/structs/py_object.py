"""Structures for CPython objects."""
from __future__ import annotations

import ctypes
from ctypes import Structure, py_object
from typing import Generic, List, Tuple, TypeVar

from typing_extensions import Self

from einspect.structs.deco import struct

_T = TypeVar("_T", bound=object)


@struct
class PyObject(Structure, Generic[_T]):
    """Defines a base PyObject Structure."""
    ob_refcnt: int
    ob_type: py_object
    # Need to use generics from typing to work for py-3.8
    _fields_: List[Tuple[str, type]]

    @property
    def mem_size(self) -> int:
        """Return the size of the PyObject in memory."""
        return ctypes.sizeof(self)

    @property
    def address(self) -> int:
        """Return the address of the PyObject."""
        return ctypes.addressof(self)

    @classmethod
    def from_object(cls, obj: _T) -> Self:
        """Create a PyObject from an object."""
        py_obj = ctypes.py_object(obj)
        addr = ctypes.c_void_p.from_buffer(py_obj).value
        if addr is None:
            raise ValueError("Object is not a valid pointer")
        return cls.from_address(addr)

    def into_object(self) -> py_object[_T]:
        """Cast the PyObject into a Python object."""
        ptr = ctypes.pointer(self)
        # Call Py_INCREF to prevent the object from being GC'd
        # pythonapi.Py_IncRef(ptr)
        obj = ctypes.cast(ptr, ctypes.py_object)
        # pythonapi.Py_IncRef(obj)
        # obj = ctypes.py_object.from_address(self._id)
        return obj


@struct
class PyVarObject(PyObject):
    """
    Defines a base PyVarObject Structure.

    https://github.com/python/cpython/blob/3.11/Include/object.h#L109-L112
    """
    ob_size: int
