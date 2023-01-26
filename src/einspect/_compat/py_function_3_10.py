from __future__ import annotations

from types import FunctionType

from einspect.structs.deco import struct
from einspect.structs.include.object_h import vectorcallfunc
from einspect.structs.py_object import PyObject
from einspect.types import ptr


@struct
class PyFunctionObject(PyObject[FunctionType, None, None]):
    globals: ptr[PyObject]
    builtins: ptr[PyObject]
    name: ptr[PyObject]
    qualname: ptr[PyObject]
    code: ptr[PyObject]  # A code object, the __code__ attribute
    defaults: ptr[PyObject]  # NULL or a tuple
    kwdefaults: ptr[PyObject]  # NULL or a dict
    closure: ptr[PyObject]  # NULL or a tuple of cell objects

    func_doc: ptr[PyObject]  # The __doc__ attribute, can be anything
    func_dict: ptr[PyObject]  # The __dict__ attribute, a dict or NULL
    func_weakreflist: ptr[PyObject]  # List of weak references
    func_module: ptr[PyObject]  # The __module__ attribute, can be anything
    func_annotations: ptr[PyObject]  # Annotations, a dict or NULL
    vectorcall: vectorcallfunc
