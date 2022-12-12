import ctypes
import gc
from typing import get_type_hints
from sys import getrefcount

from einspect import structs
from einspect.structs import PyObject
from einspect.views import view, View, ListView


tup = ("f470e2a3", "6196363168d7")
a, b = tup
print(f"{view(a).ref_count=}, {view(b).ref_count=}")

vt = view(tup)
print(f"{vt[0]=}, {vt[1]=}")
x = 1
vt[0] = ~ptr(tup)

print(tup)
print(f"{view(a).ref_count=}, {view(b).ref_count=}")
