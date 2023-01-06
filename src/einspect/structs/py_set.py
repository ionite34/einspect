from __future__ import annotations

from ctypes import Structure, POINTER

from einspect.api import Py_hash_t
from einspect.structs.deco import struct
from einspect.structs.py_object import PyObject


PySet_MINSIZE = 8
"""https://github.com/python/cpython/blob/3.11/Include/cpython/setobject.h#L18"""


@struct
class SetEntry(Structure):
    key: POINTER(PyObject)
    hash: Py_hash_t


@struct
class PySetObject(PyObject):
    """
    Defines a PySetObject Structure.

    https://github.com/python/cpython/blob/3.11/Include/cpython/setobject.h#L36-L59
    """

    fill: int
    used: int
    mask: int
    table: POINTER(SetEntry)
    hash: Py_hash_t
    finger: int
    smalltable: SetEntry * PySet_MINSIZE
    weakreflist: POINTER(PyObject)

