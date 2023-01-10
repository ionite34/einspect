"""Structures for CPython objects."""
from __future__ import annotations

import ctypes
from ctypes import Structure, pointer, py_object, pythonapi
from typing import Dict, Generic, List, Tuple, Type, TypeVar, Union

from typing_extensions import Self

from einspect.compat import Version, python_req
from einspect.protocols.delayed_bind import bind_api
from einspect.structs.deco import struct
from einspect.types import ptr

Fields = Dict[str, Union[str, Tuple[str, Type]]]

_T = TypeVar("_T")
_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


# noinspection PyPep8Naming
@struct
class PyObject(Structure, Generic[_T, _KT, _VT]):
    """Defines a base PyObject Structure."""

    ob_refcnt: int
    ob_type: pointer[Self]
    # Need to use generics from typing to work for py-3.8
    _fields_: List[Tuple[str, type]]
    _from_type_name_: str

    @property
    def mem_size(self) -> int:
        """Return the size of the PyObject in memory."""
        return ctypes.sizeof(self)

    @property
    def address(self) -> int:
        """Return the address of the PyObject."""
        return ctypes.addressof(self)

    @property
    def _orig_type_name(self) -> str | None:
        """
        Return the type repr of the original object.

        Only available if instance created with from_object.
        """
        if not hasattr(self, "_from_type_name_"):
            return None
        return self._from_type_name_

    def __eq__(self, other: Self) -> bool:
        """Return True if the PyObject is equal in address to the other."""
        if not isinstance(other, PyObject):
            return NotImplemented
        return self.address == other.address

    def __repr__(self) -> str:
        """Return a string representation of the PyObject."""
        cls_name = f"{self.__class__.__name__}"
        type_name = self._orig_type_name
        if type_name:
            cls_name += f"[{type_name}]"
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
        # Record the type name for later repr use
        type_repr = str(type(obj).__name__)
        py_obj = ctypes.py_object(obj)
        addr = ctypes.c_void_p.from_buffer(py_obj).value
        if addr is None:
            raise ValueError("Object is not a valid pointer")
        inst = cls.from_address(addr)
        inst._from_type_name_ = type_repr
        return inst

    def into_object(self) -> py_object[_T]:
        """Cast the PyObject into a Python object."""
        return ctypes.cast(self.as_ref(), ctypes.py_object)

    def as_ref(self) -> ptr[Self]:
        """Return a pointer to the PyObject."""
        return ctypes.pointer(self)

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


@struct
class PyVarObject(PyObject[_T, _KT, _VT]):
    """
    Defines a base PyVarObject Structure.

    https://github.com/python/cpython/blob/3.11/Include/object.h#L109-L112
    """

    ob_size: int

    def _format_fields_(self) -> Fields:
        return {**super()._format_fields_(), "ob_size": "Py_ssize_t"}
