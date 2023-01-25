from __future__ import annotations

from ctypes import (
    Union,
    addressof,
    c_char,
    c_char_p,
    c_uint,
    c_uint8,
    c_uint16,
    c_uint32,
    c_void_p,
    c_wchar,
    cast,
    pythonapi,
    sizeof,
)
from enum import IntEnum
from typing import Type

from typing_extensions import Annotated

from einspect.api import Py_hash_t
from einspect.protocols import bind_api
from einspect.structs.deco import struct
from einspect.structs.py_object import Fields, PyObject
from einspect.structs.traits import IsGC
from einspect.types import Array, char_p, ptr, void_p


def _PyUnicode_UTF8(obj: PyASCIIObject) -> c_char_p:
    return obj.astype(PyCompactUnicodeObject).utf8


def _PyUnicode_COMPACT_DATA(obj: PyASCIIObject) -> c_void_p:
    """Return a void pointer to the raw unicode buffer."""
    if obj.ascii:
        end = obj.address + sizeof(PyASCIIObject)
        return cast(end, c_void_p)
    return cast(obj.astype(PyCompactUnicodeObject).address + 1, c_void_p)


def _PyUnicode_NONCOMPACT_DATA(obj: PyASCIIObject) -> c_void_p:
    assert not obj.compact
    data = obj.astype(PyUnicodeObject).data.any
    assert data
    return data


def PyUnicode_DATA(obj: PyASCIIObject) -> c_void_p:
    if obj.compact:
        return _PyUnicode_COMPACT_DATA(obj)
    return _PyUnicode_NONCOMPACT_DATA(obj)


def PyUnicode_IS_COMPACT_ASCII(obj: PyASCIIObject) -> bool:
    return bool(obj.compact & obj.ascii)


def _PyUnicode_HAS_UTF8_MEMORY(obj: PyASCIIObject) -> bool:
    return (
        not PyUnicode_IS_COMPACT_ASCII(obj)
        and _PyUnicode_UTF8(obj)
        and cast(_PyUnicode_UTF8(obj), c_void_p).value != PyUnicode_DATA(obj).value
    )


def _PyUnicode_UTF8_LENGTH(obj) -> int:
    return obj.astype(PyCompactUnicodeObject).utf8_length


def PyUnicode_UTF8_LENGTH(obj: PyASCIIObject) -> int:
    assert obj.ready
    if PyUnicode_IS_COMPACT_ASCII(obj):
        return obj.length
    return _PyUnicode_UTF8_LENGTH(obj)


class State(IntEnum):
    """State of the string object (SSTATE constants)."""

    NOT_INTERNED = 0
    INTERNED_MORTAL = 1


class Kind(IntEnum):
    """
    Constants for the kind field of PyUnicodeObject.
    https://docs.python.org/3/c-api/unicode.html#c.PyUnicode_KIND
    """

    PyUnicode_1BYTE = 1
    PyUnicode_2BYTE = 2
    PyUnicode_4BYTE = 4

    def type_info(self) -> Type[c_wchar | c_uint8 | c_uint16 | c_uint32]:
        types_map = {
            0: c_wchar,
            1: c_uint8,
            2: c_uint16,
            4: c_uint32,
        }
        return types_map[int(self)]


@struct
class LegacyUnion(Union):
    any: void_p
    latin1: ptr[c_uint8]  # Py_UCS1
    ucs2: ptr[c_uint16]  # Py_UCS2
    ucs4: ptr[c_uint32]  # Py_UCS4


@struct
class PyASCIIObject(PyObject[str, None, None], IsGC):
    """
    Defines a PyUnicodeObject Structure
    """

    length: int
    hash: Annotated[int, Py_hash_t]
    interned: Annotated[int, c_uint, 1]
    kind: Annotated[int, c_uint, 3]
    compact: Annotated[int, c_uint, 1]
    ascii: Annotated[int, c_uint, 1]
    ready: Annotated[int, c_uint, 1]
    padding: Annotated[int, c_uint, 26]

    def _format_fields_(self) -> Fields:
        return {
            **super()._format_fields_(),
            "length": "Py_ssize_t",
            "hash": "Py_hash_t",
            "interned": "c_uint:1",
            "kind": "c_uint:3",
            "compact": "c_uint:1",
            "ascii": "c_uint:1",
            "ready": "c_uint:1",
            "padding": "c_uint:24",
        }

    @property
    def mem_size(self) -> int:
        """
        Return the size of the memory allocated for the string.

        Should match `unicode_sizeof_impl`
        https://github.com/python/cpython/blob/3.11/Objects/unicodeobject.c#L14120-L14149
        """
        if self.compact and self.ascii:
            size = sizeof(PyASCIIObject) + self.length + 1
        elif self.compact:
            size = sizeof(PyCompactUnicodeObject) + (self.length + 1) * Kind(self.kind)
        else:
            # If it is a two-block object, account for base object, and
            # for character block if present.
            size = sizeof(PyUnicodeObject)
            if self.astype(PyUnicodeObject).data.any:
                size += (self.length + 1) * Kind(self.kind)

        # If the wstr pointer is present, account for it unless it is shared
        # with the data pointer. Check if the data is not shared.
        if _PyUnicode_HAS_UTF8_MEMORY(self):
            size += PyUnicode_UTF8_LENGTH(self) + 1

        return size

    @property
    def buffer(self) -> Array:
        utf8_length_offset: int = PyUnicodeObject.utf8_length.offset  # type: ignore
        data_offset: int = PyUnicodeObject.data.offset  # type: ignore
        addr = addressof(self)

        if self.compact:
            # Get the str subtype type mapping
            subtype = Kind(self.kind).type_info()
            if self.ascii:
                # ASCII buffer comes right after wstr
                subtype = c_char
                addr += utf8_length_offset
            else:
                # UCS1/2/4 buffer comes right after wstr
                addr += data_offset
            return (subtype * self.length).from_address(addr)

        if self.kind == Kind.PyUnicode_1BYTE:
            return self.data.latin1  # type: ignore
        elif self.kind == Kind.PyUnicode_2BYTE:
            return self.data.ucs2  # type: ignore
        elif self.kind == Kind.PyUnicode_4BYTE:
            return self.data.ucs4  # type: ignore

        raise ValueError(f"Unknown kind: {self.kind}")

    @bind_api(pythonapi["PyUnicode_Substring"])
    def Substring(self, start: int, end: int) -> PyUnicodeObject:
        """
        Return a substring from index start to character index end (excluded).

        Negative indices are not supported.
        """

    @bind_api(pythonapi["PyUnicode_GetLength"])
    def GetLength(self) -> int:
        """Return the length of the string in code points."""


@struct
class PyCompactUnicodeObject(PyASCIIObject):
    """
    Defines a PyCompactUnicodeObject Structure

    Non-ASCII strings allocated through PyUnicode_New use the
    PyCompactUnicodeObject structure. state.compact is set, and the data
    immediately follow the structure.
    """

    utf8_length: int  # Number of bytes in utf8, excluding the \0
    utf8: char_p  # UTF-8 representation (null-terminated)

    def _format_fields_(self) -> Fields:
        return {
            **super()._format_fields_(),
            "utf8_length": "Py_ssize_t",
            "utf8": ("c_char_p", c_char_p),
        }


@struct
class PyUnicodeObject(PyCompactUnicodeObject):
    """Defines a PyUnicodeObject Structure."""

    data: LegacyUnion

    def _format_fields_(self) -> Fields:
        return {
            **super()._format_fields_(),
            "utf8_length": "Py_ssize_t",
            "utf8": "c_char_p",
            "wstr_length": "Py_ssize_t",
        }
