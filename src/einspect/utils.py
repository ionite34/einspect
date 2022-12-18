from __future__ import annotations

import ctypes
from ctypes import pythonapi
from typing import Any


def address(obj: Any) -> int:
    """Return the address of an object."""
    source = ctypes.py_object(obj)
    addr = ctypes.c_void_p.from_buffer(source).value
    if addr is None:
        raise ValueError("address: NULL object")
    return addr


def new_ref(obj: Any) -> int:
    """
    Return the address of an object, and increments refcount by 1.
    """
    addr = address(obj)
    pythonapi.Py_IncRef(ctypes.py_object(obj))
    return addr
