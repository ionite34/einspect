"""CPython API Methods and intrinsic constants."""
from __future__ import annotations

import ctypes
import typing
from collections.abc import Sequence
from ctypes import POINTER, Array, c_void_p, py_object, pythonapi, sizeof
from typing import Callable, Type, TypeVar, Union

import _ctypes
from _ctypes import _SimpleCData

from einspect.compat import Version, python_req
from einspect.protocols.delayed_bind import bind_api

__all__ = (
    "Py",
    "Py_ssize_t",
    "Py_hash_t",
    "uintptr_t",
    "PyObj_FromPtr",
    "ALIGNMENT",
    "ALIGNMENT_SHIFT",
    "align_size",
)

_T = TypeVar("_T")

Py_ssize_t = ctypes.c_ssize_t
"""Constant for type Py_ssize_t."""

Py_hash_t = ctypes.c_ssize_t
"""Constant for type Py_hash_t."""

uintptr_t = ctypes.c_uint64
"""Constant for type uintptr_t."""

ObjectOrRef = Union[py_object, object]
IntSize = Union[int, Py_ssize_t]
PyObjectPtr = POINTER(py_object)

# Alignments (must be powers of 2)
# https://github.com/python/cpython/blob/3.11/Objects/obmalloc.c#L878-L884
if sizeof(c_void_p) > 4:
    ALIGNMENT = 16
    ALIGNMENT_SHIFT = 4
else:  # pragma: no cover
    ALIGNMENT = 8
    ALIGNMENT_SHIFT = 3


# noinspection PyPep8Naming
class Py:
    """Typed methods from pythonapi."""

    @bind_api(pythonapi["Py_IncRef"])
    @staticmethod
    def IncRef(obj: object) -> None:
        """
        Increment the reference count of an object.

        https://docs.python.org/3/c-api/refcounting.html#c.Py_IncRef
        """

    @bind_api(pythonapi["Py_DecRef"])
    @staticmethod
    def DecRef(obj: object) -> None:
        """
        Decrements the reference count of an object.

        https://docs.python.org/3/c-api/refcounting.html#c.Py_DecRef
        """

    @bind_api(python_req(Version.PY_3_10) or pythonapi["Py_NewRef"])
    @staticmethod
    def NewRef(obj: object) -> object:
        """
        Return a new reference to an object and increment its refcount.

        https://docs.python.org/3/c-api/refcounting.html#c.Py_NewRef
        """

    class Tuple:
        Size: Callable[[ObjectOrRef], int] = pythonapi["PyTuple_Size"]
        """
        Return the size of a tuple object.
        https://docs.python.org/3/c-api/tuple.html#c.PyTuple_Size
        """
        Size.argtypes = (py_object,)  # type: ignore
        Size.restype = Py_ssize_t  # type: ignore

        GetItem: Callable[[ObjectOrRef, IntSize], object] = pythonapi["PyTuple_GetItem"]
        """
        Return the item at position index in the tuple o.
        https://docs.python.org/3/c-api/tuple.html#c.PyTuple_GetItem
        """
        GetItem.argtypes = (py_object, Py_ssize_t)  # type: ignore
        GetItem.restype = py_object  # type: ignore

        SetItem: Callable[[ObjectOrRef, IntSize, ObjectOrRef], None] = pythonapi[
            "PyTuple_SetItem"
        ]
        """
        Set the item at position index in the tuple o to v.
        https://docs.python.org/3/c-api/tuple.html#c.PyTuple_SetItem

        Notes:
            - This function steals a reference to v.
            - Requires tuple o to have a reference count == 1.
        """
        SetItem.argtypes = (py_object, Py_ssize_t, py_object)  # type: ignore
        SetItem.restype = None  # type: ignore

        Resize: Callable[[PyObjectPtr, IntSize], None] = pythonapi["_PyTuple_Resize"]
        """
        Resize the tuple to the specified size.
        https://docs.python.org/3/c-api/tuple.html#c._PyTuple_Resize

        Notes:
            - Not part of the documented limited C API.
            - Requires tuple o to have ref-count = 1 or size = 0
        """
        Resize.argtypes = (POINTER(py_object), Py_ssize_t)  # type: ignore
        Resize.restype = None  # type: ignore

    # noinspection PyPep8Naming
    class Type:
        @bind_api(pythonapi["PyType_Modified"])
        @staticmethod
        def Modified(obj: object) -> None:
            """
            Invalidate the internal lookup cache for the type and all of its subtypes.

            - This function must be called after any manual modification of the attributes
              or base classes of the type.
            """


PyObj_FromPtr: Callable[[IntSize], object] = _ctypes.PyObj_FromPtr
"""(Py_ssize_t ptr) -> Py_ssize_t"""


def align_size(size: int, alignment: int = ALIGNMENT) -> int:
    """Align size to alignment."""
    return (size + alignment - 1) & ~(alignment - 1)


def seq_to_array(seq: Sequence[_T] | Array[_T], dtype: _SimpleCData) -> Array:
    """Cast a Sequence to a ctypes.Array of a given type."""
    if isinstance(seq, Array):
        return seq
    arr_type = typing.cast(Type[Array[_T]], dtype * len(seq))
    return arr_type(*seq)
