"""Structures for CPython objects."""
from __future__ import annotations

import ctypes
from contextlib import contextmanager
from ctypes import Structure, py_object
from typing import Generic, List, Tuple, TypeVar, Type

from typing_extensions import Self

from einspect.protocols.delayed_bind import bind_api
from einspect.structs.deco import struct

_T = TypeVar("_T")
_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


# noinspection PyPep8Naming
@struct
class PyObject(Structure, Generic[_T, _KT, _VT]):
    """Defines a base PyObject Structure."""

    ob_refcnt: int
    ob_type: Type[_T]
    # Need to use generics from typing to work for py-3.8
    _fields_: List[Tuple[str, type]]
    _from_type_name_: str

    @bind_api(ctypes.pythonapi["Py_IncRef"])
    def IncRef(self) -> None:
        """Increment the reference count of the PyObject."""

    @bind_api(ctypes.pythonapi["Py_DecRef"])
    def DecRef(self) -> None:
        """Decrement the reference count of the PyObject."""

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

    @contextmanager
    def temp_ref(self) -> Self:
        """Create a temporary reference to the PyObject."""
        self.IncRef()
        yield self
        self.DecRef()

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
        ptr = ctypes.pointer(self)
        obj = ctypes.cast(ptr, ctypes.py_object)
        return obj


@struct
class PyVarObject(PyObject[_T, _KT, _VT]):
    """
    Defines a base PyVarObject Structure.

    https://github.com/python/cpython/blob/3.11/Include/object.h#L109-L112
    """

    ob_size: int
