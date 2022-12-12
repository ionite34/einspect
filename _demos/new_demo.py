from sys import getrefcount
from einspect import view
from einspect.api import Py
from ctypes import *


def get_tup():
    tup = (1, 2)
    tv = view(tup)
    print(f"{tv.ref_count=}")

    with tv.unsafe():
        ref = py_object(tup)
        del tup
        print(ref)
        print(f"{tv.ref_count=}")


print(get_tup())
