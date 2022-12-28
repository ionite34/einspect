from __future__ import annotations

import ctypes

from einspect.structs.deco import struct
from einspect.structs.py_object import PyObject


@struct
class PyFloatObject(PyObject):
    """
    Defines a PyFloatObject Structure.

    https://github.com/python/cpython/blob/3.11/Include/cpython/floatobject.h
    """

    ob_fval: ctypes.c_double
