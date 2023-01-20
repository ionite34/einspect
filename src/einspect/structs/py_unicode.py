from __future__ import annotations

from ctypes import (
    Union,
    addressof,
    c_char,
    c_char_p,
    c_int64,
    c_uint,
    c_uint8,
    c_uint16,
    c_uint32,
    c_void_p,
    c_wchar,
)
from enum import IntEnum
from typing import Type

from typing_extensions import Annotated

from einspect.structs.deco import struct
from einspect.structs.py_object import PyObject
from einspect.types import Array, ptr


class State(IntEnum):
    NOT_INTERNED = 0
    INTERNED_MORTAL = 1
    INTERNED_IMMORTAL = 2


class Kind(IntEnum):
    """
    Constants for the kind field of PyUnicodeObject.
    https://docs.python.org/3/c-api/unicode.html#c.PyUnicode_KIND
    """

    PyUnicode_WCHAR = 0
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
    any: c_void_p
    latin1: ptr[c_uint8]  # Py_UCS1
    ucs2: ptr[c_uint16]  # Py_UCS2
    ucs4: ptr[c_uint32]  # Py_UCS4


@struct
class PyUnicodeObject(PyObject):
    """
    Defines a PyUnicodeObject Structure
    """

    length: int
    hash: Annotated[int, c_int64]
    interned: Annotated[int, c_uint, 2]
    kind: Annotated[int, c_uint, 3]
    compact: Annotated[int, c_uint, 1]
    ascii: Annotated[int, c_uint, 1]
    ready: Annotated[int, c_uint, 1]
    padding: Annotated[int, c_uint, 24]
    wstr: ptr[c_wchar]
    # Fields after this do not exist if ascii
    utf8_length: int
    utf8: c_char_p
    wstr_length: int
    # Fields after this do not exist if compact
    data: LegacyUnion

    @property
    def buffer(self) -> Array:
        cls = type(self)
        addr = addressof(self)

        # Annotate some types transformed by ctypes.Structure
        data_offset: int = cls.data.offset  # type: ignore
        utf8_length_offset: int = cls.utf8_length.offset  # type: ignore

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

        if self.kind == Kind.PyUnicode_WCHAR:
            # Note that this goes with wstr_length, not length!
            return self.wstr  # type: ignore
        elif self.kind == Kind.PyUnicode_1BYTE:
            return self.data.latin1  # type: ignore
        elif self.kind == Kind.PyUnicode_2BYTE:
            return self.data.ucs2  # type: ignore
        elif self.kind == Kind.PyUnicode_4BYTE:
            return self.data.ucs4  # type: ignore

        raise ValueError(f"Unknown kind: {self.kind}")
