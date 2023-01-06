from __future__ import annotations

from einspect.structs.deco import struct
from einspect.structs.mapping_proxy import MappingProxyObject
from einspect.structs.py_dict import PyDictObject
from einspect.structs.py_list import PyListObject
from einspect.structs.py_long import PyLongObject
from einspect.structs.py_object import PyObject, PyVarObject
from einspect.structs.py_tuple import PyTupleObject
from einspect.structs.py_unicode import PyUnicodeObject
from einspect.structs.py_bool import PyBoolObject
from einspect.structs.py_set import PySetObject

__all__ = (
    "deco",
    "PyObject",
    "PyVarObject",
    "PyTupleObject",
    "PyListObject",
    "PyLongObject",
    "PyBoolObject",
    "PyUnicodeObject",
    "PyDictObject",
    "MappingProxyObject",
    "PySetObject",
)
