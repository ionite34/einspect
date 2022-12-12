from ctypes import *

PyObject_GC_UnTrack = pythonapi["PyObject_GC_UnTrack"]
PyObject_GC_UnTrack.argtypes = (py_object,)
PyObject_GC_UnTrack.restype = None

PyObject_GC_Del = pythonapi["PyObject_GC_Del"]
PyObject_GC_Del.argtypes = (py_object,)
PyObject_GC_Del.restype = None

Py_IncRef = pythonapi["Py_IncRef"]
Py_IncRef.argtypes = (py_object,)

Py_DecRef = pythonapi["Py_DecRef"]
Py_DecRef.argtypes = (py_object,)

obj = ("abc", "def", "def")
src = [5, 6, 7]

Py_IncRef(py_object(src))
Py_DecRef(py_object(obj))
# PyObject_GC_UnTrack(cast(id(obj) - 16, POINTER(py_object)))
# memmove(id(obj), id(src), src.__sizeof__())
memmove(id(obj) - 16, id(src) - 16, src.__sizeof__() + 16)
# PyObject_GC_UnTrack(byref(obj))
# PyObject_GC_Del(py_object(src))
print(obj)


