from __future__ import annotations

from ctypes import (
    POINTER,
    Structure,
    addressof,
    c_char,
    c_char_p,
    c_uint,
    c_ulong,
    cast,
    pointer,
    py_object,
    pythonapi,
)
from typing import Any, Type, TypeVar

from typing_extensions import Annotated, Self

from einspect.protocols import bind_api
from einspect.structs.include.descrobject_h import PyGetSetDef, PyMemberDef
from einspect.structs.include.methodobject_h import PyMethodDef
from einspect.structs.include.object_h import *
from einspect.structs.py_object import PyObject, PyVarObject
from einspect.structs.slots_map import get_slot
from einspect.types import NULL, ptr

__all__ = ("PyTypeObject",)

_T = TypeVar("_T")

DEFAULT = object()


# noinspection PyPep8Naming
class PyTypeObject(PyVarObject[_T, None, None]):
    """
    Defines a PyTypeObject Structure.

    https://github.com/python/cpython/blob/3.11/Doc/includes/typestruct.h

    ..
        source: Include/cpython/object.h (struct _typeobject)
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
    tp_subclasses: ptr[PyObject]  # for static builtin types this is an index
    tp_weaklist: ptr[PyObject]
    tp_del: destructor

    # Type attribute cache version tag. Added in version 2.6
    tp_version_tag: Annotated[int, c_uint]

    tp_finalize: destructor
    tp_vectorcall: vectorcallfunc

    # bitset of which type-watchers care about this type
    tp_watched: c_char

    def __new__(cls, __obj: Type[_T] = DEFAULT, **kwargs):
        """
        Create a new PyTypeObject.

        One positional argument can be passed to create a PyTypeObject from a type object.
        Otherwise, keyword arguments of fields can be provided.

        Args:
            __obj: A Python object to create a PyTypeObject from.
            **kwargs: Fields to create a PyObject from.
        """
        if __obj is not DEFAULT:
            # If already a PyObject
            if isinstance(__obj, PyObject):
                return cls.from_address(__obj.address)
            # Use from_object
            return cls.from_object(__obj)

        # Base case
        return Structure.__new__(cls)

    def __repr__(self) -> str:
        """Return a string representation of the PyTypeObject."""
        cls_name = f"{self.__class__.__name__}"
        type_name = self.tp_name.decode()
        return f"<{cls_name}[{type_name}] at {self.address:#04x}>"

    @classmethod
    def from_object(cls, obj: Type[_T] | type) -> PyTypeObject[Type[_T]]:
        return super().from_object(obj)  # type: ignore

    def setattr_safe(self, name: str, value: Any) -> None:
        """Set an attribute on the type object. Uses custom overrides if available."""
        # Resolve the slot into an attr name, if any
        if (slot := get_slot(name)) is None:
            self.SetAttr(name, value)
            return

        # Get PyMethods pointer, if null, error
        if slot.ptr_type and not getattr(self, slot.parts[0]):
            raise TypeError(
                f"PyTypeObject {self} has no allocated {slot.ptr_type} {slot.parts[0]!r}"
            )

        # Get type as element 1 of the field tuple
        if field := self._fields_map_.get(slot.name):
            field_type = field[1]
            # For c_char_p types, set encoded bytes
            if field_type is c_char_p:
                return setattr(self, slot.name, value.encode("utf-8"))
            # For ptr[PyObject] types, set PyObject pointer
            elif field_type == POINTER(PyObject):
                return setattr(self, slot.name, PyObject.from_object(value).as_ref())

        # If not a recognized slot, set with PyObject_SetAttr api
        self.SetAttr(name, value)

    def _try_del_tp_dict(self, name: str) -> None:
        """Try to delete a key from the type's dict, if tp_dict is not NULL."""
        if self.tp_dict:
            type_dict: dict[str, Any] = self.tp_dict.contents.into_object()
            if name in type_dict:
                del type_dict[name]

    def delattr_safe(self, name: str) -> None:
        """Delete an attribute on the type object. Uses custom overrides if available."""
        # If not a recognized slot, delete with normal api
        if (slot := get_slot(name)) is None:
            self.DelAttr(name)
            self._try_del_tp_dict(name)
            return

        # Slot is in a PyMethods sub-struct
        if slot.ptr_type:
            # Get PyMethods pointer, if null, we don't have to delete anything
            if not (method_ptr := getattr(self, slot.parts[0])):
                return
            # Set slot function pointer on PyMethods to null
            method = method_ptr.contents
            setattr(method, slot.parts[1], NULL)
            self._try_del_tp_dict(name)
            return

        # Get type as element 1 of the field tuple
        field = self._fields_map_.get(slot.name)
        field_type = field[1]

        # Overrides
        # For c_char_p types, set encoded bytes
        if field_type is c_char_p:
            setattr(self, slot.name, b"")
        # For ptr[PyObject] types, set PyObject pointer
        elif field_type == POINTER(PyObject):
            setattr(self, slot.name, POINTER(PyObject)())
        # Otherwise, set to null
        setattr(self, slot.name, NULL)

        # Delete from type dict
        self._try_del_tp_dict(name)

    def is_gc(self) -> bool:
        """
        Return True if the type has GC support.

        https://docs.python.org/3/c-api/type.html#c.PyType_IS_GC
        https://github.com/python/cpython/blob/3.11/Include/objimpl.h#L160-L161
        """
        return bool(self.tp_flags & TpFlags.HAVE_GC)

    @bind_api(pythonapi["PyType_Ready"])
    def Ready(self) -> int:
        """Finalize a type object."""

    @bind_api(pythonapi["PyType_Modified"])
    def Modified(self) -> None:
        """Mark the type as modified."""

    @bind_api(pythonapi["_PyObject_New"])
    def New(self) -> ptr[PyObject]:
        """Create a new object of the type."""

    @bind_api(pythonapi["_PyObject_GC_New"])
    def GC_New(self) -> ptr[PyObject]:
        """Create a new object of the type with GC support."""

    @bind_api(pythonapi["_PyObject_NewVar"])
    def NewVar(self, nitems: int) -> ptr[PyVarObject]:
        """Create a new variable object of the type."""

    @bind_api(pythonapi["_PyObject_GC_NewVar"])
    def GC_NewVar(self, nitems: int) -> ptr[PyVarObject]:
        """Create a new variable object of the type with GC support."""


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


class TypeNewWrapper:
    def __init__(self, tp_new: newfunc, wrap_type: Type[_T]):
        # Cast tp_new to remove Structure binding
        self._tp_new = cast(tp_new, newfunc)
        self._type = wrap_type
        # Store the original slot wrapper as well, for restoring
        self._orig_slot_fn = self._type.__new__
        self.__name__ = "__new__"

    def __repr__(self):
        return (
            f"<wrapped method __new__ of type object at {addressof(self._tp_new):#04x}>"
        )

    def __call__(self, *args: tuple, **kwds: dict):
        """Implements `tp_new_wrapper` with a modified safety check."""
        if not isinstance(args, tuple) or len(args) < 1:
            raise TypeError(f"{self.__name__}.__new__(): not enough arguments")

        subtype = args[0]

        if not isinstance(subtype, type):
            raise TypeError(
                f"{self.__name__}.__new__(X): X is not a type object ({type(subtype).__name__})"
            )

        if not issubclass(subtype, self._type):
            raise TypeError(
                f"{self.__name__}.__new__({subtype.__name__}): "
                f"{subtype.__name__} is not a subtype of {self.__name__}"
            )

        # Check that we don't do something silly and unsafe like
        # object.__new__(dict). To do this, we check that the most derived
        # base that's not a heap type is this type.
        staticbase = PyTypeObject.from_object(subtype).as_ref()
        while staticbase and staticbase[0].tp_new == self._tp_new:
            staticbase = staticbase[0].tp_base

        # We modify a safety check for (staticbase->tp_new == type->tp_new)
        # to instead check for type identity.
        # This is so orig().__new__ can be called within a custom __new__.
        # Semantically, this is the same as the original check.
        # Also bypass this check if the type is a heap type, and _type is object / type.
        if staticbase and (staticbase_obj := staticbase[0]):
            if (staticbase_obj.tp_flags & TpFlags.HEAPTYPE) and (
                self._type is object or self._type is type
            ):
                staticbase_obj = None
            if staticbase_obj and staticbase_obj != PyTypeObject.from_object(
                self._type
            ):
                raise TypeError(
                    f"{self._type.__name__}.__new__({subtype.__name__}): "
                    f"is not safe, use {staticbase[0].tp_name}.__new__()"
                )

        # object.__new__ takes no arguments, so don't pass any if we're calling it
        if self._type is object:
            return self._tp_new(subtype, (), {})

        return self._tp_new(subtype, args[1:], kwds)
