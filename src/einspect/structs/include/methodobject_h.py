from __future__ import annotations

from ctypes import PYFUNCTYPE, Structure, c_char_p, c_int, py_object

from typing_extensions import Annotated

from einspect.structs import struct

__all__ = ("PyMethodDef", "PyCFunction")

PyCFunction = PYFUNCTYPE(py_object, py_object, py_object)


@struct
class PyMethodDef(Structure):
    ml_name: Annotated[bytes, c_char_p]
    ml_meth: PyCFunction
    ml_flags: Annotated[int, c_int]
    ml_doc: Annotated[bytes, c_char_p]
