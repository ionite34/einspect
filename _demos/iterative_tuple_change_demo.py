from einspect.api import Py
from ctypes import *


def get_tup():
    t = py_object(("cat", "dog"))
    print(t.value)
    print(id(t.value))
    Py.DecRef(t)

    for item in ["snake", "py", "rs"]:
        size = len(t.value)
        Py.IncRef(item)
        Py.DecRef(t)
        Py.Tuple.Resize(byref(t), size + 1)
        Py.Tuple.SetItem(t, size, item)
        Py.IncRef(t)

        print(t.value)
        print(id(t.value))

    Py.IncRef(t)
    return t.value


print(get_tup())
