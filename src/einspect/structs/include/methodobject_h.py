from __future__ import annotations

from ctypes import PYFUNCTYPE, Structure, c_char, c_char_p, c_int, py_object

from typing_extensions import Annotated

from einspect.structs import struct

__all__ = ("PyMethodDef", "PyCFunction")

PyCFunction = PYFUNCTYPE(py_object, py_object, py_object)


@struct
class PyMethodDef(Structure):
    ml_name: c_char
    ml_meth: PyCFunction
    ml_flags: Annotated[int, c_int]
    ml_doc: c_char_p
