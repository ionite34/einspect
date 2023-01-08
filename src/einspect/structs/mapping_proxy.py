from __future__ import annotations

from types import MappingProxyType
from typing import TypeVar

from einspect.structs.deco import struct
from einspect.structs.py_dict import PyDictObject
from einspect.structs.py_object import PyObject

__all__ = ("MappingProxyObject",)

_KT = TypeVar("_KT")
_VT_co = TypeVar("_VT_co", covariant=True)


@struct
class MappingProxyObject(PyObject[MappingProxyType, _KT, _VT_co]):
    """
    Defines a mappingproxyobject Structure.

    https://github.com/python/cpython/blob/3.11/Objects/descrobject.c#L1027-L1030
    """

    mapping: PyDictObject[_KT, _VT_co]

    @classmethod
    def from_object(
        cls, obj: MappingProxyType[_KT, _VT_co]
    ) -> MappingProxyObject[MappingProxyType, _KT, _VT_co]:
        """Create a MappingProxyObject from an object."""
        return super().from_object(obj)  # type: ignore
