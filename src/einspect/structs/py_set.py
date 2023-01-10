from __future__ import annotations

from ctypes import Array, Structure, pointer
from typing import Generic, TypeVar

from typing_extensions import Annotated

from einspect.api import Py_hash_t
from einspect.structs.deco import struct
from einspect.structs.py_object import PyObject
from einspect.types import ptr

_T = TypeVar("_T")

PySet_MINSIZE = 8
"""https://github.com/python/cpython/blob/3.11/Include/cpython/setobject.h#L18"""


@struct
class SetEntry(Structure, Generic[_T]):
    key: pointer[PyObject[_T, None, None]]
    hash: Annotated[int, Py_hash_t]  # noqa: A003


@struct(
    fields=[
        ("smalltable", SetEntry * PySet_MINSIZE),
    ]
)
class PySetObject(PyObject[set, None, _T]):
    """
    Defines a PySetObject Structure.

    https://github.com/python/cpython/blob/3.11/Include/cpython/setobject.h#L36-L59
    """

    fill: int  # Number active and dummy entries
    used: int  # Number active entries
    mask: int  # The table contains mask + 1 slots
    table: ptr[SetEntry[_T]]
    hash: Annotated[int, Py_hash_t]  # noqa: A003
    finger: int
    smalltable: Array[SetEntry[_T]]
    weakreflist: ptr[PyObject]

    @classmethod
    def from_object(cls, obj: set[_T]) -> PySetObject[_T]:
        return cls.from_address(id(obj))
