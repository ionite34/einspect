import ctypes
from typing import Any


def from_ptr(addr: int) -> Any:
    """Casts a pointer to a Python object."""
    return ctypes.cast(addr, ctypes.py_object).value
