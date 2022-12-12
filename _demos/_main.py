import ctypes
import gc
from typing import get_type_hints
from sys import getrefcount

from einspect import structs
from einspect.views import view, View, ListView


def from_ptr(addr):
    """Casts a pointer to a Python object."""
    return ctypes.cast(addr, ctypes.py_object).value


tup = ("a", "b", "c")

tview = view(tup)

print(tview)
print(f"{tview[0]=}, {tview[1]=}, {tview[2]=}")
# tview[0] = "abcdef"
print(tup)

print(view((2, 3, 5))._pyobject._ob_item_0)
print(view((2, 3, 5))[0])
