from __future__ import annotations

from ctypes import PYFUNCTYPE, c_char_p, c_int, c_void_p, py_object

from typing_extensions import Annotated

from einspect.structs.deco import Struct

__all__ = ("getter", "setter", "PyMemberDef", "PyGetSetDef")

getter = PYFUNCTYPE(py_object, py_object, py_object)
setter = PYFUNCTYPE(c_int, py_object, py_object, c_void_p)


class PyMemberDef(Struct):
    name: c_char_p
    type: Annotated[int, c_int]
    offset: int
    flags: Annotated[int, c_int]
    doc: c_char_p


class PyGetSetDef(Struct):
    name: c_char_p
    get: getter
    set: setter
    doc: c_char_p
    closure: c_void_p
