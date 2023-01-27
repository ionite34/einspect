from __future__ import annotations

import sys

from einspect.structs.deco import struct
from einspect.structs.py_object import PyObject, PyVarObject  # Req import first
from einspect.structs.py_type import PyTypeObject, TpFlags
from einspect.structs.py_long import PyLongObject  # Req before PyBoolObject
from einspect.structs.py_bool import PyBoolObject
from einspect.structs.py_float import PyFloatObject
from einspect.structs.py_list import PyListObject
from einspect.structs.py_tuple import PyTupleObject
from einspect.structs.py_set import PySetObject, SetEntry
from einspect.structs.py_cfunction import PyCFunctionObject

# Req before PyMappingProxyObject
from einspect.structs.py_dict import PyDictObject, PyDictKeysObject, PyDictValues
from einspect.structs.mapping_proxy import MappingProxyObject

# Compatibility override for py_function
if sys.version_info > (3, 11):
    import einspect.structs.py_function as py_function
    from einspect.structs.py_function import PyFunctionObject
elif sys.version_info > (3, 10):
    import einspect._compat.py_function_3_10 as py_function
    from einspect._compat.py_function_3_10 import PyFunctionObject
else:
    import einspect._compat.py_function_3_9 as py_function
    from einspect._compat.py_function_3_9 import PyFunctionObject

# Compatibility override for Python 3.12
if sys.version_info < (3, 12):
    import einspect.structs.py_unicode as py_unicode
    from einspect.structs.py_unicode import (
        PyUnicodeObject,
        PyCompactUnicodeObject,
        PyASCIIObject,
        Kind,
        State,
    )
else:
    import einspect._compat.py_unicode_3_12 as py_unicode
    from einspect._compat.py_unicode_3_12 import (
        PyUnicodeObject,
        PyCompactUnicodeObject,
        PyASCIIObject,
        Kind,
        State,
    )

__all__ = (
    "struct",
    "PyObject",
    "PyVarObject",
    "PyTypeObject",
    "TpFlags",
    "PyTupleObject",
    "PyListObject",
    "PyLongObject",
    "PyBoolObject",
    "PyFloatObject",
    "PyUnicodeObject",
    "PyFunctionObject",
    "PyCFunctionObject",
    "State",
    "Kind",
    "PyCompactUnicodeObject",
    "py_function",
    "py_unicode",
    "PyASCIIObject",
    "PyDictObject",
    "PyDictKeysObject",
    "PyDictValues",
    "MappingProxyObject",
    "PySetObject",
    "SetEntry",
)
