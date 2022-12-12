import ctypes
from ctypes import memmove, pytonapi, py_object

dll = ctypes.CDLL('libc.dylib')

dll.malloc.argtypes = (ctypes.c_size_t,)
dll.malloc.restype = ctypes.c_void_p

dll.free.argtypes = (ctypes.c_void_p,)
dll.free.restype = None

dll.realloc.argtypes = (ctypes.c_size_t, ctypes.c_size_t)
dll.realloc.restype = ctypes.c_void_p

Py_IncRef = pythonapi["Py_IncRef"]
Py_IncRef.argtypes = (py_object,)

obj = 500
src = (1, 2)

# Realloc the 16 byte memory block before id(obj)
dll.malloc(id(obj))

Py_IncRef(py_object(src))
memmove(id(obj) - 16, id(src) - 16, src.__sizeof__() + 16)

print(500)
