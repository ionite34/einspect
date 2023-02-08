from __future__ import annotations

import ctypes

from einspect.structs.py_object import PyObject


class PyFloatObject(PyObject[float, None, None]):
    """
    Defines a PyFloatObject Structure.

    https://github.com/python/cpython/blob/3.11/Include/cpython/floatobject.h
    """

    ob_fval: ctypes.c_double
