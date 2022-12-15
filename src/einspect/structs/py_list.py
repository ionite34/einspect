from __future__ import annotations

import ctypes

from einspect.structs.deco import struct
from einspect.structs.py_object import PyVarObject


@struct
class PyListObject(PyVarObject):
    """
    Defines a PyListObject Structure.

    https://github.com/python/cpython/blob/3.11/Include/cpython/listobject.h
    """
    ob_item: ctypes.POINTER(ctypes.c_void_p)
    allocated: ctypes.c_long
