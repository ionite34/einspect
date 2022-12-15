from __future__ import annotations

import ctypes
from ctypes import Array
from enum import IntEnum


from einspect.structs.deco import struct
from einspect.structs.py_object import PyObject


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

    def type(self):
        if self == self.PyUnicode_WCHAR:
            return ctypes.c_wchar
        elif self == self.PyUnicode_1BYTE:
            return ctypes.c_uint8
        elif self == self.PyUnicode_2BYTE:
            return ctypes.c_uint16
        elif self == self.PyUnicode_4BYTE:
            return ctypes.c_uint32
        else:
            raise ValueError(f"Unknown kind: {self}")


@struct
class LegacyUnion(ctypes.Union):
    any: ctypes.c_void_p
    latin1: ctypes.POINTER(ctypes.c_uint8)  # Py_UCS1
    ucs2: ctypes.POINTER(ctypes.c_uint16)  # Py_UCS2
    ucs4: ctypes.POINTER(ctypes.c_uint32)  # Py_UCS4


@struct
class PyUnicodeObject(PyObject):
    """
    Defines a PyUnicodeObject Structure
    """
    length: int
    hash: ctypes.c_int64
    _interned: ctypes.c_uint = 2
    _kind: ctypes.c_uint = 3
    compact: ctypes.c_uint = 1
    ascii: ctypes.c_uint = 1
    ready: ctypes.c_uint = 1
    padding: ctypes.c_uint = 24
    wstr: ctypes.POINTER(ctypes.c_wchar)
    # Fields after this do not exist if ascii
    utf8_length: int
    utf8: ctypes.c_char_p
    wstr_length: int
    # Fields after this do not exist if compact
    data: LegacyUnion

    @property
    def interned(self) -> State:
        return State(self._interned)

    @interned.setter
    def interned(self, value: State):
        self._interned = value.value  # type: ignore

    @property
    def kind(self) -> Kind:
        return Kind(self._kind)

    @kind.setter
    def kind(self, value: Kind):
        self._kind = value.value  # type: ignore

    @property
    def buffer(self) -> Array:
        cls = type(self)
        addr = ctypes.addressof(self)

        # Annotate some types transformed by ctypes.Structure
        data_offset: int = cls.data.offset  # type: ignore
        utf8_length_offset: int = cls.utf8_length.offset  # type: ignore

        if self.compact:
            # Get the str subtype type mapping
            subtype = self.kind.type()
            if self.ascii:
                # ASCII buffer comes right after wstr
                subtype = ctypes.c_char
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

