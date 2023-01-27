from __future__ import annotations

from types import BuiltinFunctionType
from typing import Callable, TypeVar

from einspect.structs.deco import struct
from einspect.structs.include.methodobject_h import PyMethodDef
from einspect.structs.include.object_h import vectorcallfunc
from einspect.structs.py_object import PyObject
from einspect.types import ptr

_T = TypeVar("_T", BuiltinFunctionType, Callable)


@struct
class PyCFunctionObject(PyObject[_T, None, None]):
    m_ml: ptr[PyMethodDef]  # Description of the C function to call
    m_self: ptr[PyObject]  # Passed as 'self' arg to the C func, can be NULL
    m_module: ptr[PyObject]  # The __module__ attribute, can be anything
    m_weakreflist: ptr[PyObject]  # List of weak references
    vectorcall: vectorcallfunc

    @classmethod
    def from_object(cls, obj: _T) -> PyCFunctionObject[_T]:
        return super().from_object(obj)  # type: ignore
