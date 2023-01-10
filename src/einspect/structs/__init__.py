from __future__ import annotations

from einspect.structs.deco import struct
from einspect.structs.py_object import PyObject, PyVarObject  # Req import first
from einspect.structs.py_type import PyTypeObject
from einspect.structs.py_long import PyLongObject  # Req before PyBoolObject
from einspect.structs.py_bool import PyBoolObject
from einspect.structs.py_unicode import PyUnicodeObject
from einspect.structs.py_list import PyListObject
from einspect.structs.py_tuple import PyTupleObject
from einspect.structs.py_set import PySetObject
from einspect.structs.py_dict import PyDictObject  # Req before PyMappingProxyObject
from einspect.structs.mapping_proxy import MappingProxyObject

__all__ = (
    "struct",
    "PyObject",
    "PyVarObject",
    "PyTypeObject",
    "PyTupleObject",
    "PyListObject",
    "PyLongObject",
    "PyBoolObject",
    "PyUnicodeObject",
    "PyDictObject",
    "MappingProxyObject",
    "PySetObject",
)
