from __future__ import annotations

from ctypes import (
    POINTER,
    c_char,
    c_char_p,
    c_uint,
    c_ulong,
    c_void_p,
    pointer,
    py_object,
    pythonapi,
)
from typing import Any, Type, TypeVar

from typing_extensions import Annotated, Self

from einspect.protocols import bind_api
from einspect.structs.deco import struct
from einspect.structs.include.descrobject_h import PyGetSetDef, PyMemberDef
from einspect.structs.include.methodobject_h import PyMethodDef
from einspect.structs.include.object_h import *
from einspect.structs.py_object import PyObject, PyVarObject
from einspect.structs.slots_map import get_slot
from einspect.types import ptr

__all__ = ("PyTypeObject",)

_T = TypeVar("_T")


# noinspection PyPep8Naming
@struct
class PyTypeObject(PyVarObject[_T, None, None]):
    """
    Defines a PyTypeObject Structure.

    https://github.com/python/cpython/blob/3.11/Doc/includes/typestruct.h
    """

    tp_name: Annotated[bytes, c_char_p]
    # For allocation
    tp_basicsize: int
    tp_itemsize: int
    # Methods to implement standard operations
    tp_dealloc: destructor
    tp_vectorcall_offset: int
    tp_getattr: getattrfunc
    tp_setattr: setattrfunc
    # formerly known as tp_compare (Python 2) or tp_reserved (Python 3)
    tp_as_async: ptr[PyAsyncMethods]

    tp_repr: reprfunc

    # Method suites for standard classes
    tp_as_number: ptr[PyNumberMethods]
    tp_as_sequence: ptr[PySequenceMethods]
    tp_as_mapping: ptr[PyMappingMethods]

    # More standard operations (here for binary compatibility)
    tp_hash: hashfunc
    tp_call: ternaryfunc
    tp_str: reprfunc
    tp_getattro: getattrofunc
    tp_setattro: setattrofunc

    # Functions to access object as input/output buffer
    tp_as_buffer: ptr[PyBufferProcs]

    # Flags to define presence of optional/expanded features
    tp_flags: Annotated[int, c_ulong]

    tp_doc: Annotated[bytes, c_char_p]  # Documentation string

    # Assigned meaning in release 2.0
    # call function for all accessible objects
    tp_traverse: traverseproc

    tp_clear: inquiry  # delete references to contained objects

    # Assigned meaning in release 2.1
    # rich comparisons
    tp_richcompare: richcmpfunc

    tp_weaklistoffset: int  # weak reference enabler

    # Iterators
    tp_iter: getiterfunc
    tp_iternext: iternextfunc

    # Attribute descriptor and subclassing stuff
    tp_methods: ptr[PyMethodDef]
    tp_members: ptr[PyMemberDef]
    tp_getset: ptr[PyGetSetDef]

    # Strong reference on a heap type, borrowed reference on a static type
    tp_base: pointer[Self]
    tp_dict: ptr[PyObject]
    tp_descr_get: descrgetfunc
    tp_descr_set: descrsetfunc
    tp_dictoffset: int
    tp_init: initproc
    tp_alloc: allocfunc
    tp_new: newfunc
    tp_free: freefunc  # Low-level free-memory routine
    tp_is_gc: inquiry  # For PyObject_IS_GC
    tp_bases: ptr[PyObject]
    tp_mro: ptr[PyObject]  # method resolution order
    tp_cache: ptr[PyObject]
    tp_subclasses: c_void_p  # for static builtin types this is an index
    tp_weaklist: ptr[PyObject]
    tp_del: destructor

    # Type attribute cache version tag. Added in version 2.6
    tp_version_tag: Annotated[int, c_uint]

    tp_finalize: destructor
    tp_vectorcall: vectorcallfunc

    # bitset of which type-watchers care about this type
    tp_watched: c_char

    @classmethod
    def from_object(cls, obj: Type[_T]) -> PyTypeObject[Type[_T]]:
        return super().from_object(obj)  # type: ignore

    def setattr_safe(self, name: str, value: Any) -> None:
        """Set an attribute on the type object. Uses custom overrides if available."""
        # Resolve the slot into an attr name, if any
        if (slot := get_slot(name)) is not None:
            # Override c_char_p types
            if type_object_fields.get(slot.name) is c_char_p:
                setattr(self, slot.name, value.encode())
                return
            # Override ptr[PyObject] types
            if type_object_fields.get(slot.name) == ptr[PyObject]:
                setattr(self, slot.name, PyObject.from_object(value).as_ref())
                return
        self.SetAttr(name, value)

    @bind_api(pythonapi["PyType_Modified"])
    def Modified(self) -> None:
        """Mark the type as modified."""

    def is_gc(self) -> bool:
        """
        Return True if the type has GC support.

        https://docs.python.org/3/c-api/type.html#c.PyType_IS_GC
        https://github.com/python/cpython/blob/3.11/Include/objimpl.h#L160-L161
        """
        return bool(self.tp_flags & TpFlags.HAVE_GC)


# Mapping of CField name to type
# noinspection PyProtectedMember
type_object_fields = {name: t for name, t, *_ in PyTypeObject._fields_}


# Patch PyTypeObject back into PyObject
def _patch_py_object():
    # noinspection PyProtectedMember
    fields = PyObject._fields_
    fields[1] = ("ob_type", POINTER(PyTypeObject))
    offset = object.__basicsize__ + tuple.__itemsize__ * 3
    py_object.from_address(id(PyObject.ob_type) + offset).value = POINTER(PyTypeObject)


_patch_py_object()
