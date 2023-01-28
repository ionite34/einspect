"""CPython API Methods and intrinsic constants."""
from __future__ import annotations

import ctypes
from collections.abc import Sequence
from ctypes import Array, c_size_t, c_void_p, pythonapi, sizeof
from typing import Any, Callable, TypeVar

import _ctypes
from typing_extensions import Annotated

from einspect.compat import Version, python_req
from einspect.protocols.delayed_bind import bind_api

__all__ = (
    "Py",
    "Py_ssize_t",
    "Py_hash_t",
    "uintptr_t",
    "PTR_SIZE",
    "PyObj_FromPtr",
    "ALIGNMENT",
    "ALIGNMENT_SHIFT",
    "align_size",
    "address",
    "seq_to_array",
)

from einspect.types import NULL, Pointer

_T = TypeVar("_T")
_CT = TypeVar("_CT")

Py_ssize_t = ctypes.c_ssize_t
"""Constant for type Py_ssize_t."""

Py_hash_t = ctypes.c_ssize_t
"""Constant for type Py_hash_t."""

uintptr_t = ctypes.c_uint64
"""Constant for type uintptr_t."""

PTR_SIZE = sizeof(c_void_p)
"""Size of a pointer in bytes."""

# Alignments (must be powers of 2)
# https://github.com/python/cpython/blob/3.11/Objects/obmalloc.c#L878-L884
if sizeof(c_void_p) > 4:
    ALIGNMENT = 16
    ALIGNMENT_SHIFT = 4
else:  # pragma: no cover
    ALIGNMENT = 8
    ALIGNMENT_SHIFT = 3


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
        @bind_api(pythonapi["PyTuple_Size"])
        @staticmethod
        def Size(obj: tuple) -> int:
            """
            Return the size of a tuple object.
            https://docs.python.org/3/c-api/tuple.html#c.PyTuple_Size
            """

        @bind_api(pythonapi["PyTuple_GetItem"])
        @staticmethod
        def GetItem(obj: tuple, index: int) -> object:
            """
            Return the item at position index in the tuple o.
            https://docs.python.org/3/c-api/tuple.html#c.PyTuple_GetItem
            """

        @bind_api(pythonapi["PyTuple_SetItem"])
        @staticmethod
        def SetItem(obj: tuple, index: int, value: object) -> None:
            """
            Set the item at position index in the tuple o to v.
            https://docs.python.org/3/c-api/tuple.html#c.PyTuple_SetItem

            Notes:
                - This function steals a reference to v.
                - Requires tuple o to have a reference count == 1.
            """

        @bind_api(pythonapi["_PyTuple_Resize"])
        @staticmethod
        def Resize(obj: tuple, size: int) -> None:
            """
            Resize the tuple to the specified size.
            https://docs.python.org/3/c-api/tuple.html#c._PyTuple_Resize

            Notes:
                - Not part of the documented limited C API.
                - Requires tuple o to have ref-count = 1 or size = 0.
            """

    class Type:
        @bind_api(pythonapi["PyType_Modified"])
        @staticmethod
        def Modified(obj: object) -> None:
            """
            Invalidate the internal lookup cache for the type and all of its subtypes.

            - This function must be called after any manual modification of the attributes
              or base classes of the type.
            """

    class Mem:
        @bind_api(pythonapi["PyMem_Malloc"])
        @staticmethod
        def Malloc(n: Annotated[int, c_size_t]) -> c_void_p:
            """
            Allocates n bytes and returns a pointer of type void* to the allocated memory,
            or NULL if the request fails.

            Requesting zero bytes returns a distinct non-NULL pointer if possible,
            as if PyMem_Malloc(1) had been called instead. The memory will not
            have been initialized in any way.

            https://docs.python.org/3/c-api/memory.htm
            """

        @bind_api(pythonapi["PyMem_Calloc"])
        @staticmethod
        def Calloc(
            nelem: Annotated[int, c_size_t], elsize: Annotated[int, c_size_t]
        ) -> c_void_p:
            """
            Allocates nelem elements each whose size in bytes is elsize and
            returns  The memory is initialized to zeros.

            Requesting zero elements or elements of size zero bytes
            returns a distinct non-NULL pointer if possible,
            as if PyMem_Calloc(1, 1) had been called instead.

            Args:
                nelem: Number of elements.
                elsize: Size of each element in bytes.

            Returns:
                A pointer to the allocated memory, or NULL if the request fails.
            """

        @bind_api(pythonapi["PyMem_Realloc"])
        @staticmethod
        def Realloc(p: c_void_p, n: Annotated[int, c_size_t]) -> c_void_p:
            """
            Resizes the memory block pointed to by p to n bytes.
            The contents will be unchanged to the minimum of the old and the new sizes.

            Args:
                p: Pointer to the memory block to be resized.
                n: New size in bytes.

            Returns:
                Pointer p, or NULL if request fails (p remains a valid pointer).
            """


PyObj_FromPtr: Callable[[int], object] = _ctypes.PyObj_FromPtr
"""(Py_ssize_t ptr) -> Py_ssize_t"""


def address(obj: Any) -> int:
    """Return the address of a python object. Same as id()."""
    source = ctypes.py_object(obj)
    addr = ctypes.c_void_p.from_buffer(source).value
    if addr is None:
        raise ValueError("address: NULL object")  # pragma: no cover
    return addr


def align_size(size: int, alignment: int = ALIGNMENT) -> int:
    """Align size to alignment."""
    return (size + alignment - 1) & ~(alignment - 1)


def seq_to_array(
    seq: Sequence[_T] | Array[_T], dtype: type[_CT], py_obj_try_cast: bool = True
) -> Array[_CT]:
    """Cast a Sequence to a ctypes.Array of a given type."""
    if isinstance(seq, Array):
        return seq

    arr_type = dtype * len(seq)

    if py_obj_try_cast and issubclass(dtype, Pointer):
        dtype_r = dtype._type_
        if hasattr(dtype_r, "try_from"):
            # If we find a NULL singleton, don't set it.
            arr = arr_type()
            for i, v in enumerate(seq):
                if v is not NULL:
                    arr[i] = dtype_r.try_from(v).with_ref().as_ref()
            return arr

    return arr_type(*seq)
