import _ctypes
import ctypes
from ctypes import py_object

PyTuple_Size = ctypes.pythonapi.PyTuple_Size
PyTuple_Size.argtypes = (py_object,)
PyTuple_Size.restype = ctypes.c_ssize_t

tup = (1, 2, 3)
tup_id = id(tup)

py_obj = py_object(_ctypes.PyObj_FromPtr(tup_id))
print(py_obj)

size = PyTuple_Size(py_obj)
print(size)
