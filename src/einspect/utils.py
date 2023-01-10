from __future__ import annotations

import ctypes
from typing import Any

from einspect.api import Py


def address(obj: Any) -> int:
    """Return the address of an object."""
    source = ctypes.py_object(obj)
    addr = ctypes.c_void_p.from_buffer(source).value
    if addr is None:
        raise ValueError("address: NULL object")  # pragma: no cover
    return addr


def new_ref(obj: Any) -> int:
    """
    Return the address of an object, and increments refcount by 1.
    """
    addr = address(obj)
    Py.IncRef(obj)
    return addr
