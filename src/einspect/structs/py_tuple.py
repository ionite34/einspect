from __future__ import annotations

import ctypes
from ctypes import pythonapi

from einspect.api import Py_ssize_t
from einspect.structs.deco import struct
from einspect.structs.py_object import PyVarObject


@struct
class PyTupleObject(PyVarObject):
    """
    Defines a PyTupleObject Structure.

    https://github.com/python/cpython/blob/3.11/Include/cpython/tupleobject.h
    """
    # Size of this array is only known after creation
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
        arr = Py_ssize_t * self.ob_size
        return arr.from_address(items_addr)


PyTupleObject.GetItem = pythonapi["PyTuple_GetItem"]
"""(PyObject *o, Py_ssize_t index) -> Py_ssize_t"""
PyTupleObject.GetItem.argtypes = (ctypes.POINTER(PyTupleObject), Py_ssize_t)
PyTupleObject.GetItem.restype = ctypes.py_object

PyTupleObject.SetItem = pythonapi["PyTuple_SetItem"]
"""(PyObject *o, Py_ssize_t index, PyObject *v) -> int"""
PyTupleObject.SetItem.argtypes = (ctypes.POINTER(PyTupleObject), Py_ssize_t, ctypes.py_object)
PyTupleObject.SetItem.restype = None

PyTupleObject.Resize = pythonapi["_PyTuple_Resize"]
"""(PyObject *o, Py_ssize_t index, PyObject *v) -> int"""
PyTupleObject.Resize.argtypes = (ctypes.POINTER(PyTupleObject), Py_ssize_t)
PyTupleObject.Resize.restype = None
