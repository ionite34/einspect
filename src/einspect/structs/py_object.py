"""Structures for CPython objects."""
from __future__ import annotations

import ctypes
import warnings
from contextlib import suppress
from ctypes import POINTER, Structure, c_void_p, pythonapi
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    List,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
)

from typing_extensions import Annotated, Self

from einspect.api import PTR_SIZE, address, align_size
from einspect.compat import Version, python_req
from einspect.protocols.delayed_bind import bind_api
from einspect.protocols.type_parse import is_ctypes_type
from einspect.structs.deco import struct
from einspect.structs.py_gc import PyGC_Head
from einspect.structs.traits import AsRef, IsGC
from einspect.types import ptr

if TYPE_CHECKING:
    from einspect.structs import PyTypeObject

__all__ = ("PyObject", "PyVarObject", "Fields", "py_get", "py_set")

Fields = Dict[str, Union[str, Tuple[str, Type]]]

_T = TypeVar("_T")
_KT = TypeVar("_KT")
_VT = TypeVar("_VT")
_ST = TypeVar("_ST", bound=Structure)

DEFAULT = object()


def py_get(obj_ptr: ptr[PyObject]) -> object | None:
    """
    Get a PyObject pointer value.

    If the pointer is NULL, return None.
    """
    return obj_ptr.contents.into_object() if obj_ptr else None


def py_set(obj_ptr: ptr[PyObject], value: object | PyObject | ptr[PyObject]) -> None:
    """
    Set a PyObject pointer value on a View.

    If the attribute exists and points to a PyObject, it will be DecRef'd.
    The value will be IncRef'd before being set.
    """
    # Get and DecRef current
    if obj_ptr:
        obj_ptr.contents.DecRef()
    # Set new
    obj_ptr.contents = PyObject.try_from(value).with_ref()


@struct
class PyObject(Structure, AsRef, Generic[_T, _KT, _VT]):
    """Defines a base PyObject Structure."""

    ob_refcnt: int
    ob_type: Annotated[ptr[PyTypeObject[Type[_T]]], c_void_p]

    _fields_: List[Union[Tuple[str, type], Tuple[str, type, int]]]

    @overload
    def __new__(cls, __obj: _T):
        ...

    @overload
    def __new__(cls, *, ob_refcnt: int = 1, ob_type: ptr[PyTypeObject], **kwargs):
        ...

    def __new__(cls, __obj: _T = DEFAULT, **kwargs):
        """
        Create a new PyObject.

        One positional argument can be passed to create a PyObject from an object.
        Otherwise, keyword arguments of fields can be provided.

        Args:
            __obj: A Python object to create a PyObject from.
            **kwargs: Fields to create a PyObject from.
        """
        from einspect.structs.py_type import PyTypeObject

        # Base case
        if __obj is DEFAULT and not kwargs:
            return super().__new__(cls)
        if __obj is not DEFAULT:
            # If already a PyObject
            if isinstance(__obj, PyObject):
                return cls.from_address(__obj.address)
            # Use from_object
            return cls.from_object(__obj)
        # Check kwargs
        if "ob_type" not in kwargs:
            raise TypeError("Missing required keyword-argument field 'ob_type'")

        new_ob_size: int = kwargs.get("ob_size", 0).__index__()
        new_ob_type = PyTypeObject.try_from(kwargs["ob_type"])

        if issubclass(cls, IsGC):
            res = (
                new_ob_type.GC_NewVar(new_ob_size)
                if issubclass(cls, PyVarObject)
                else new_ob_type.GC_New()
            )
        else:
            res = (
                new_ob_type.NewVar(new_ob_size)
                if issubclass(cls, PyVarObject)
                else new_ob_type.New()
            )
        return res.contents.astype(cls)

    @property
    def mem_size(self) -> int:
        """Return the size of the PyObject in memory."""
        return ctypes.sizeof(self)

    @property
    def address(self) -> int:
        """Return the address of the PyObject."""
        return ctypes.addressof(self)

    def __eq__(self, other: Self) -> bool:
        """Return True if the PyObject is equal in address to the other."""
        if not isinstance(other, PyObject):
            return NotImplemented
        return self.address == other.address

    def __repr__(self) -> str:
        """Return a string representation of the PyObject."""
        cls_name = f"{self.__class__.__name__}"
        # For generic PyObjects, add the type name
        if self.__class__ in (PyObject, PyVarObject):
            with suppress(ValueError):
                obj_type = self.ob_type.contents
                cls_name += f"[{obj_type.tp_name.decode()}]"
        return f"<{cls_name} at {self.address:#04x}>"

    def _format_fields_(self) -> Fields:
        """
        Return an attribute mapping for info display.

        Returns:
            Dict mapping of field to type-hint or (type-hint, cast type)
        """
        return {"ob_refcnt": "Py_ssize_t", "ob_type": "*PyTypeObject"}

    @classmethod
    def from_object(cls, obj: _T) -> Self:
        """Create a PyObject from an object."""
        return cls.from_address(address(obj))

    @classmethod
    def from_gc(cls, gc: PyGC_Head) -> Self:
        """Create a PyObject from a PyGC_Head struct."""
        addr = ctypes.addressof(gc) + ctypes.sizeof(PyGC_Head)
        return cls.from_address(addr)

    @classmethod
    def try_from(cls, obj_or_ptr: PyObject | ptr[PyObject] | object) -> Self:
        """Create a PyObject from a PyObject, pointer to a PyObject, or object."""
        # noinspection PyUnresolvedReferences
        if isinstance(obj_or_ptr, ctypes._Pointer):
            obj = obj_or_ptr.contents
        else:
            obj = obj_or_ptr
        # For ctypes types
        if is_ctypes_type(type(obj)):
            if isinstance(obj, PyObject):
                return cls.from_object(obj.into_object())
            # raise if not a PyObject
            raise TypeError(f"Cannot create PyObject from {obj_or_ptr!r}")
        # For Python objects
        return cls.from_object(obj)

    def into_object(self) -> _T:
        """Cast the PyObject into a Python object."""
        py_obj = ctypes.cast(self.as_ref(), ctypes.py_object)
        return py_obj.value

    def astype(self, dtype: Type[_ST]) -> _ST:
        """Cast the PyObject into another PyObject type."""
        return dtype.from_address(self.address)

    def with_ref(self, n: int = 1) -> Self:
        """Increment the reference count of the PyObject by n. Return self."""
        self.ob_refcnt += n
        return self

    def is_gc(self) -> bool:
        """
        Returns True if the object implements the GC protocol.

        The object cannot be tracked by the garbage collector if False.

        https://github.com/python/cpython/blob/3.11/Include/internal/pycore_object.h#L209-L216
        """
        return (type_obj := self.ob_type.contents).is_gc() and (
            not type_obj.tp_is_gc or type_obj.tp_is_gc(self.into_object())
        )

    def as_gc(self) -> PyGC_Head:
        """Return the PyGC_Head struct of this object."""
        addr = self.address - ctypes.sizeof(PyGC_Head)
        return PyGC_Head.from_address(addr)  # type: ignore

    def gc_is_tracked(self) -> bool:
        """Return True if the PyObject is currently tracked by the GC."""
        return self.as_gc()._gc_next != 0

    def gc_may_be_tracked(self) -> bool:
        """
        Return True if the PyObject may be tracked by
        the GC in the future, or already is.

        https://github.com/python/cpython/blob/3.11/Include/internal/pycore_gc.h#L28-L32
        """
        if not self.is_gc():
            return False
        if self.ob_type.contents.into_object() is tuple:
            return self.gc_is_tracked()
        return True

    def instance_dict(self) -> ptr[PyObject[dict, Any, Any]] | None:
        """
        Return the instance dict of the PyObject.

        An offset override can be set by `__st_dictoffset__`. It should be
        relative to the address of the PyObject.

        https://docs.python.org/3/c-api/typeobj.html#c.PyTypeObject.tp_dictoffset
        """
        # Get the tp_dictoffset of the type
        offset = self.ob_type.contents.tp_dictoffset
        # If 0, the type does not have a dict
        if offset == 0:
            return None
        # For -1, the type uses the 3.12 Managed Dict feature
        if offset == -1:
            # Check that the flag is set
            from einspect.structs import TpFlags

            if not self.ob_type.contents.tp_flags & TpFlags.MANAGED_DICT:
                raise RuntimeError(
                    "type has a __dictoffset__ of -1, but tp_flags does not have TpFlags.MANAGED_DICT"
                )
            # Materialize the dict
            inst_dict = self.GetAttr("__dict__")
            return PyObject.from_object(inst_dict).as_ref()
        # For > 0, start from the address of the PyObject
        if offset > 0:
            addr = self.address + offset
        # For < 0, start after the struct
        else:
            # If not a PyVarObject, use __basic_size__ instead
            if getattr(self, "ob_size", None) is None:
                size = self.ob_type.contents.tp_basicsize
            else:
                size = align_size(self.mem_size, PTR_SIZE)
                # Increase size by pointer size since mem_size at this point
                # excludes the instance dict (unlike __sizeof__)
                size += PTR_SIZE
            addr = self.address + size + offset
        # Return the pointer
        return POINTER(PyObject).from_address(addr)

    @bind_api(python_req(Version.PY_3_10) or pythonapi["Py_NewRef"])
    def NewRef(self) -> object:
        """Returns new reference of the PyObject."""

    @bind_api(pythonapi["Py_IncRef"])
    def IncRef(self) -> None:
        """Increment the reference count of the PyObject."""

    @bind_api(pythonapi["Py_DecRef"])
    def DecRef(self) -> None:
        """Decrement the reference count of the PyObject."""

    @bind_api(pythonapi["PyObject_GetAttr"])
    def GetAttr(self, name: str) -> object:
        """Return the attribute of the PyObject."""

    @bind_api(pythonapi["PyObject_SetAttr"])
    def SetAttr(self, name: str, value: object) -> int:
        """Set the attribute of the PyObject."""


# We don't want this visible to type-checking but `PyObject.__init__`
# needs to ignore the `__obj` positional argument
orig_init = PyObject.__init__  # type: ignore


def _PyObject__init__(self, *args, **kwargs) -> None:
    if len(args) > 1:
        warnings.warn(
            "Positional arguments to PyObject.__init__ are not supported, use keywords instead.",
            UserWarning,
        )
    return orig_init(self, **kwargs)  # type: ignore


PyObject.__init__ = _PyObject__init__


@struct
class PyVarObject(PyObject[_T, _KT, _VT]):
    """
    Defines a base PyVarObject Structure.

    https://github.com/python/cpython/blob/3.11/Include/object.h#L109-L112
    """

    ob_size: int

    def _format_fields_(self) -> Fields:
        return {**super()._format_fields_(), "ob_size": "Py_ssize_t"}
