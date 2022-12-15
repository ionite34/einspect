import ctypes
from typing import Any


def get_addr(cfunc):
    ptr = ctypes.c_void_p.from_address(ctypes.addressof(cfunc))
    return ptr.value


def from_ptr(addr: int) -> Any:
    """Casts a pointer to a Python object."""
    return ctypes.cast(addr, ctypes.py_object).value
