import ctypes
from ctypes import pythonapi
from typing import Any


def address(obj: Any) -> int:
    """Return the address of an object."""
    return ctypes.c_void_p.from_buffer(ctypes.py_object(obj)).value


def new_ref(obj: Any) -> int:
    """
    Return the address of an object, and increments refcount by 1.
    """
    addr = address(obj)
    pythonapi.Py_IncRef(ctypes.py_object(obj))
    return addr
