from __future__ import annotations

from ctypes import (
    POINTER,
    Structure,
    c_char,
    c_ssize_t,
    c_uint8,
    c_uint32,
    c_uint64,
    c_void_p,
    pythonapi,
)
from typing import Dict, TypeVar

from einspect.api import Py_ssize_t
from einspect.protocols.delayed_bind import bind_api
from einspect.structs.deco import struct
from einspect.structs.py_object import PyObject

__all__ = ("PyDictObject",)

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


@struct
class DictKeysObject(Structure):
    """
    Defines a DictKeysObject Structure.

    https://github.com/python/cpython/blob/3.11/Include/internal/pycore_dict.h#L87-L125
    """

    dk_refcnt: Py_ssize_t
    dk_log2_size: c_uint8
    dk_log2_index_bytes: c_uint8
    dk_kind: c_uint8
    dk_version: c_uint32
    dk_usable: Py_ssize_t
    dk_nentries: Py_ssize_t
    dk_indices: POINTER(c_char)


# noinspection PyPep8Naming
@struct
class PyDictObject(PyObject[dict, _KT, _VT]):
    """
    Defines a PyDictObject Structure.

    https://github.com/python/cpython/blob/3.11/Include/cpython/dictobject.h
    """

    # Number of items in the dictionary
    ma_used: c_ssize_t
    # Dictionary version: globally unique, changes on modification
    ma_version_tag: c_uint64
    ma_keys: POINTER(DictKeysObject)
    # If ma_values is NULL, the table is "combined": keys and values
    # are stored in ma_keys. Otherwise, keys are stored in ma_keys
    # and values are stored in ma_values
    ma_values: POINTER(c_void_p)

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
