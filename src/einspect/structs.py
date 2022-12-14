"""Structures for CPython objects."""
from __future__ import annotations

import _ctypes
import ctypes
from ctypes import Structure, pythonapi, py_object, POINTER
from typing import get_type_hints, TypeVar, Type, Generic, List, Tuple

from typing_extensions import Self


from einspect import api

Py_ssize_t = ctypes.c_ssize_t

_T = TypeVar("_T", bound=Type[Structure])


def struct(cls: _T) -> _T:
    """Decorator to create a ctypes Structure subclass."""
    fields = []
    for name, type_hint in get_type_hints(cls).items():
        if name.startswith("_") and name.endswith("_"):
            continue
        if name not in cls.__annotations__:
            continue
        fields.append((name, type_hint))
    cls._fields_ = fields
    return cls


@struct
class PyObject(Structure, Generic[_T]):
    """Defines a base PyObject Structure."""
    ob_refcnt: Py_ssize_t
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
    ob_size: Py_ssize_t


@struct
class PyLongObject(PyVarObject):
    """
    Defines a PyLongObject Structure.

    https://github.com/python/cpython/blob/3.11/Include/cpython/longintrepr.h#L79-L82
    """
    _ob_digit_0: ctypes.c_uint32 * 0

    @property
    def mem_size(self) -> int:
        """Return the size of the PyObject in memory."""
        # Need to add size(uint32) * ob_size to our base size
        base = super().mem_size
        return base + ctypes.sizeof(ctypes.c_uint32) * self.ob_size

    @property
    def ob_digit(self):
        # Note PyLongObject uses the sign bit of ob_size to indicate its own sign
        # ob_size < 0 means the number is negative
        # ob_size > 0 means the number is positive
        # ob_size == 0 means the number is zero
        # The true size of the ob_digit array is abs(ob_size)
        items_addr = ctypes.addressof(self._ob_digit_0)
        size = abs(int(self.ob_size))  # type: ignore
        return (ctypes.c_uint32 * size).from_address(items_addr)

    @property
    def value(self) -> int:
        digit: int
        if self.ob_size == 0:
            return 0
        val = sum(digit * 1 << (30*i) for i, digit in enumerate(self.ob_digit))
        size: int = self.ob_size  # type: ignore
        return val * (-1 if size < 0 else 1)


@struct
class PyListObject(PyVarObject):
    """
    Defines a PyListObject Structure.

    https://github.com/python/cpython/blob/3.11/Include/cpython/listobject.h
    """
    ob_item: ctypes.POINTER(ctypes.c_void_p)
    allocated: ctypes.c_long


@struct
class PyTupleObject(PyVarObject):
    """
    Defines a PyTupleObject Structure.

    https://github.com/python/cpython/blob/3.11/Include/cpython/tupleobject.h
    """
    # Size of this array is not known at compile time
    # store only
    _ob_item_0: Py_ssize_t * 0

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
        size = int(self.ob_size)  # type: ignore
        return (Py_ssize_t * size).from_address(items_addr)

    def container_inc_ref(self) -> None:
        """Increment the refcount of all child references."""
        for item in self.ob_item:
            pythonapi.Py_IncRef(api.PyObj_FromPtr(item))


PyTupleObject.GetItem = pythonapi["PyTuple_GetItem"]
"""(PyObject *o, Py_ssize_t index) -> Py_ssize_t"""
PyTupleObject.GetItem.argtypes = (ctypes.POINTER(PyTupleObject), Py_ssize_t)
# PyTupleObject.GetItem.restype = ctypes.c_void_p
PyTupleObject.GetItem.restype = ctypes.py_object

PyTupleObject.SetItem = pythonapi["PyTuple_SetItem"]
"""(PyObject *o, Py_ssize_t index, PyObject *v) -> int"""
PyTupleObject.SetItem.argtypes = (ctypes.POINTER(PyTupleObject), Py_ssize_t, ctypes.py_object)
PyTupleObject.SetItem.restype = None

PyTupleObject.Resize = pythonapi["_PyTuple_Resize"]
"""(PyObject *o, Py_ssize_t index, PyObject *v) -> int"""
PyTupleObject.Resize.argtypes = (ctypes.POINTER(PyTupleObject), Py_ssize_t)
PyTupleObject.Resize.restype = None

# PyTupleObject.SET_ITEM = pythonapi["PyTuple_SET_ITEM"]
# """(PyObject *o, Py_ssize_t index, PyObject *v) -> int"""
# PyTupleObject.SET_ITEM.argtypes = (ctypes.POINTER(PyTupleObject), Py_ssize_t, ctypes.c_void_p)
