from __future__ import annotations

from ctypes import PYFUNCTYPE, Structure, c_char_p, c_int, c_void_p, py_object

from typing_extensions import Annotated

from einspect.structs import struct

__all__ = ("getter", "setter", "PyMemberDef", "PyGetSetDef")

getter = PYFUNCTYPE(py_object, py_object, py_object)
setter = PYFUNCTYPE(c_int, py_object, py_object, c_void_p)


@struct
class PyMemberDef(Structure):
    name: c_char_p
    type: Annotated[int, c_int]
    offset: int
    flags: Annotated[int, c_int]
    doc: c_char_p


@struct
class PyGetSetDef(Structure):
    name: c_char_p
    get: getter
    set: setter
    doc: c_char_p
    closure: c_void_p
