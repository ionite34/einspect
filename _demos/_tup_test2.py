import _ctypes
from ctypes import *

py_size = PYFUNCTYPE(c_ssize_t, py_object)
get_item = PYFUNCTYPE(c_ssize_t, py_object, c_ssize_t)

PyTuple_GetItem = get_item(pythonapi.PyTuple_GetItem)
PyTuple_Size = py_size(pythonapi.PyTuple_Size)

tup = (1, 2, 3)
tup_id = id(tup)
py_obj = py_object(_ctypes.PyObj_FromPtr(tup_id))
print(py_obj)

size = PyTuple_Size(py_obj)
print(size)
