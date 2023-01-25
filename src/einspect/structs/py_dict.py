from __future__ import annotations

from ctypes import (
    POINTER,
    Structure,
    _SimpleCData,
    addressof,
    c_char,
    c_int8,
    c_int16,
    c_int32,
    c_int64,
    c_uint8,
    c_uint32,
    c_uint64,
    pythonapi,
)
from typing import Dict, TypeVar

from typing_extensions import Annotated

from einspect.protocols.delayed_bind import bind_api
from einspect.structs.deco import struct
from einspect.structs.py_object import Fields, PyObject
from einspect.structs.traits import Display, IsGC
from einspect.types import Array, ptr

__all__ = ("PyDictObject",)


_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


@struct
class PyDictKeysObject(Structure, Display):
    """
    Defines a DictKeysObject Structure.

    https://github.com/python/cpython/blob/3.11/Include/internal/pycore_dict.h#L87-L125
    """

    dk_refcnt: int
    dk_log2_size: Annotated[int, c_uint8]
    dk_log2_index_bytes: Annotated[int, c_uint8]
    dk_kind: Annotated[int, c_uint8]
    dk_version: Annotated[int, c_uint32]
    dk_usable: int
    dk_nentries: int
    # Actual hash table of dk_size entries. It holds indices in dk_entries,
    # or DKIX_EMPTY(-1) or DKIX_DUMMY(-2).
    # Indices must be: 0 <= indice < USABLE_FRACTION(dk_size).
    #
    # The size in bytes of an indice depends on dk_size:
    # - 1 byte if dk_size <= 0xff (char*)
    # - 2 bytes if dk_size <= 0xffff (int16_t*)
    # - 4 bytes if dk_size <= 0xffffffff (int32_t*)
    # - 8 bytes otherwise (int64_t*)
    #
    # Dynamically sized, SIZEOF_VOID_P is minimum.
    _dk_indices: c_int8 * 0

    @property
    def dk_indices(self) -> Array[int]:
        items_addr = addressof(self._dk_indices)
        item_type = self._dk_indices_type()[0]
        arr = item_type * self._dk_size
        return arr.from_address(items_addr)

    @property
    def _dk_size(self) -> int:
        return 1 << self.dk_log2_size

    def _dk_indices_type(self) -> tuple[_SimpleCData, str]:
        if self._dk_size <= 0xFF:
            return c_char, "c_char"
        elif self._dk_size <= 0xFFFF:
            return c_int16, "c_int16"
        elif self._dk_size <= 0xFFFFFFFF:  # pragma: no branch
            return c_int32, "c_int32"
        return c_int64, "c_int64"  # pragma: no cover

    def _format_fields_(self) -> Fields:
        indice_type, indice_name = self._dk_indices_type()
        return {
            "dk_refcnt": "Py_ssize_t",
            "dk_log2_size": "c_uint8",
            "dk_log2_index_bytes": "c_uint8",
            "dk_kind": "c_uint8",
            "dk_version": "c_uint32",
            "dk_usable": "Py_ssize_t",
            "dk_nentries": "Py_ssize_t",
            "dk_indices": f"Array[{indice_name}]",
        }


@struct
class PyDictValues(Structure, Display):
    values: ptr[PyObject]


@struct
class PyDictObject(PyObject[dict, _KT, _VT], IsGC):
    """
    Defines a PyDictObject Structure.

    https://github.com/python/cpython/blob/3.11/Include/cpython/dictobject.h
    """

    # Number of items in the dictionary
    ma_used: int
    # Dictionary version: globally unique, changes on modification
    ma_version_tag: Annotated[int, c_uint64]
    ma_keys: ptr[PyDictKeysObject]
    # If ma_values is NULL, the table is "combined": keys and values
    # are stored in ma_keys. Otherwise, keys are stored in ma_keys
    # and values are stored in ma_values
    ma_values: ptr[PyDictValues]

    def _format_fields_(self) -> Fields:
        return {
            **super()._format_fields_(),
            "ma_used": "Py_ssize_t",
            "ma_version_tag": "c_uint64",
            "ma_keys": "*PyDictKeysObject",
            "ma_values": "*PyDictValues",
        }

    @bind_api(pythonapi["PyDict_GetItem"])
    def GetItem(self, key: _KT) -> POINTER(PyObject):
        """Return a pointer to the value object at key, or NULL if the key is not found."""

    @bind_api(pythonapi["PyDict_SetItem"])
    def SetItem(self, key: _KT, val: _VT) -> int:
        """
        Set a value to a given key.

        This function does not steal a reference to val.

        Returns:
            0 on success or -1 on failure.

        Raises:
            TypeError: if the key is not hashable.
        """

    @bind_api(pythonapi["PyDict_DelItem"])
    def DelItem(self, key: _KT) -> int:
        """
        Remove the entry with key.

        Returns:
            0 on success or -1 on failure.

        Raises:
            TypeError: if the key is not hashable.
            KeyError: if the key is not present.
        """

    @classmethod
    def from_object(cls, obj: Dict[_KT, _VT]) -> PyDictObject[_KT, _VT]:
        """Create a PyDictObject from an object."""
        return super().from_object(obj)  # type: ignore
