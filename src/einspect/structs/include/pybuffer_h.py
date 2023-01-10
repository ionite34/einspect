from __future__ import annotations

from ctypes import PYFUNCTYPE, Structure, c_int, c_void_p, py_object

from einspect.api import Py_ssize_t
from einspect.structs import PyObject, struct
from einspect.types import ptr

__all__ = ("Py_buffer", "getbufferproc", "releasebufferproc")


# noinspection PyPep8Naming
@struct
class Py_buffer(Structure):
    buf: c_void_p
    obj: ptr[PyObject]  # owned reference
    len: Py_ssize_t
    itemsize: Py_ssize_t  # Py_ssize_t so it can be pointed to by strides in simple case
    readonly: c_int
    ndim: c_int
    format: c_void_p
    shape: ptr[Py_ssize_t]
    strides: ptr[Py_ssize_t]
    suboffsets: ptr[Py_ssize_t]
    internal: c_void_p


getbufferproc = PYFUNCTYPE(c_int, py_object, Py_buffer, c_int)
releasebufferproc = PYFUNCTYPE(None, py_object, Py_buffer)
