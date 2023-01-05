from __future__ import annotations

from einspect.structs import PyLongObject
from einspect.structs.deco import struct

__all__ = ("PyBoolObject",)


@struct
class PyBoolObject(PyLongObject):
    """
    Defines a PyBoolObject Structure.

    https://github.com/python/cpython/blob/3.11/Objects/boolobject.c#L198-L206
    """
