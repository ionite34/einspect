"""https://github.com/python/cpython/blob/3.11/Include/object.h"""
from ctypes import PYFUNCTYPE, Structure, c_char_p, c_int, c_void_p, py_object
from enum import IntEnum

from einspect.api import Py_ssize_t
from einspect.structs.deco import struct
from einspect.types import ptr

__all__ = (
    "unaryfunc",
    "binaryfunc",
    "ternaryfunc",
    "inquiry",
    "lenfunc",
    "ssizeargfunc",
    "ssizessizeargfunc",
    "ssizeobjargproc",
    "ssizessizeobjargproc",
    "objobjargproc",
    "objobjproc",
    "visitproc",
    "traverseproc",
    "freefunc",
    "destructor",
    "getattrfunc",
    "getattrofunc",
    "setattrfunc",
    "setattrofunc",
    "reprfunc",
    "hashfunc",
    "richcmpfunc",
    "getiterfunc",
    "iternextfunc",
    "descrgetfunc",
    "descrsetfunc",
    "initproc",
    "newfunc",
    "allocfunc",
    "vectorcallfunc",
    "sendfunc",
    "PyAsyncMethods",
    "PyNumberMethods",
    "PyMappingMethods",
    "PySequenceMethods",
)


# Function types
# https://github.com/python/cpython/blob/3.11/Include/object.h#L196-L227

# typedef PyObject * (*unaryfunc)(PyObject *);
unaryfunc = PYFUNCTYPE(py_object, py_object)
# typedef PyObject * (*binaryfunc)(PyObject *, PyObject *);
binaryfunc = PYFUNCTYPE(py_object, py_object, py_object)
# typedef PyObject * (*ternaryfunc)(PyObject *, PyObject *, PyObject *);
ternaryfunc = PYFUNCTYPE(py_object, py_object, py_object, py_object)
# typedef int (*inquiry)(PyObject *);
inquiry = PYFUNCTYPE(c_int, py_object)
# typedef Py_ssize_t (*lenfunc)(PyObject *);
lenfunc = PYFUNCTYPE(Py_ssize_t, py_object)
# typedef PyObject *(*ssizeargfunc)(PyObject *, Py_ssize_t);
ssizeargfunc = PYFUNCTYPE(py_object, py_object, Py_ssize_t)
# typedef PyObject *(*ssizessizeargfunc)(PyObject *, Py_ssize_t, Py_ssize_t);
ssizessizeargfunc = PYFUNCTYPE(py_object, py_object, Py_ssize_t, Py_ssize_t)
# typedef int(*ssizeobjargproc)(PyObject *, Py_ssize_t, PyObject *);
ssizeobjargproc = PYFUNCTYPE(c_int, py_object, Py_ssize_t, py_object)
# typedef int(*ssizessizeobjargproc)(PyObject *, Py_ssize_t, Py_ssize_t, PyObject *);
ssizessizeobjargproc = PYFUNCTYPE(c_int, py_object, Py_ssize_t, Py_ssize_t, py_object)
# typedef int(*objobjargproc)(PyObject *, PyObject *, PyObject *);
objobjargproc = PYFUNCTYPE(c_int, py_object, py_object, py_object)

# typedef int (*objobjproc)(PyObject *, PyObject *);
objobjproc = PYFUNCTYPE(c_int, py_object, py_object)
# typedef int (*visitproc)(PyObject *, void *);
visitproc = PYFUNCTYPE(c_int, py_object, c_void_p)
# typedef int (*traverseproc)(PyObject *, visitproc, void *);
traverseproc = PYFUNCTYPE(c_int, py_object, visitproc, c_void_p)

# typedef void (*freefunc)(void *);
freefunc = PYFUNCTYPE(None, c_void_p)
# typedef void (*destructor)(PyObject *);
destructor = PYFUNCTYPE(None, py_object)
# typedef PyObject *(*getattrfunc)(PyObject *, char *);
getattrfunc = PYFUNCTYPE(py_object, py_object, c_char_p)
# typedef PyObject *(*getattrofunc)(PyObject *, PyObject *);
getattrofunc = PYFUNCTYPE(py_object, py_object, py_object)
# typedef int (*setattrfunc)(PyObject *, char *, PyObject *);
setattrfunc = PYFUNCTYPE(c_int, py_object, c_char_p, py_object)
# typedef int (*setattrofunc)(PyObject *, PyObject *, PyObject *);
setattrofunc = PYFUNCTYPE(c_int, py_object, py_object, py_object)
# typedef PyObject *(*reprfunc)(PyObject *);
reprfunc = PYFUNCTYPE(py_object, py_object)
# typedef Py_hash_t (*hashfunc)(PyObject *);
hashfunc = PYFUNCTYPE(Py_ssize_t, py_object)
# typedef PyObject *(*richcmpfunc) (PyObject *, PyObject *, int);
richcmpfunc = PYFUNCTYPE(py_object, py_object, py_object, c_int)
# typedef PyObject *(*getiterfunc) (PyObject *);
getiterfunc = PYFUNCTYPE(py_object, py_object)
# typedef PyObject *(*iternextfunc) (PyObject *);
iternextfunc = PYFUNCTYPE(py_object, py_object)

# typedef PyObject *(*descrgetfunc) (PyObject *, PyObject *, PyObject *);
descrgetfunc = PYFUNCTYPE(py_object, py_object, py_object, py_object)
# typedef int (*descrsetfunc) (PyObject *, PyObject *, PyObject *);
descrsetfunc = PYFUNCTYPE(c_int, py_object, py_object, py_object)
# typedef int (*initproc)(PyObject *, PyObject *, PyObject *);
initproc = PYFUNCTYPE(c_int, py_object, py_object, py_object)
# typedef PyObject *(*newfunc)(PyTypeObject *, PyObject *, PyObject *);
newfunc = PYFUNCTYPE(py_object, py_object, py_object, py_object)
# typedef PyObject *(*allocfunc)(PyTypeObject *, Py_ssize_t);
allocfunc = PYFUNCTYPE(py_object, py_object, Py_ssize_t)

# typedef PyObject *(*vectorcallfunc)(PyObject *callable, PyObject *const *args, size_t nargsf, PyObject *kwnames)
vectorcallfunc = PYFUNCTYPE(py_object, py_object, ptr[py_object], Py_ssize_t, py_object)


class PySendResult(IntEnum):
    """Result of calling PyIter_Send."""

    PYGEN_RETURN = 0
    PYGEN_ERROR = -1
    PYGEN_NEXT = 1


# typedef PySendResult (*sendfunc)(PyObject *iter, PyObject *value, PyObject **result);
sendfunc = PYFUNCTYPE(c_int, py_object, py_object, ptr[py_object])


@struct
class PyAsyncMethods(Structure):
    am_await: unaryfunc
    am_aiter: unaryfunc
    am_anext: unaryfunc
    am_send: sendfunc


@struct
class PyNumberMethods(Structure):
    """
    Number implementations must check *both*
    arguments for proper type and implement the necessary conversions
    in the slot functions themselves.
    """

    nb_add: binaryfunc
    nb_subtract: binaryfunc
    nb_multiply: binaryfunc
    nb_remainder: binaryfunc
    nb_divmod: binaryfunc
    nb_power: ternaryfunc
    nb_negative: unaryfunc
    nb_positive: unaryfunc
    nb_absolute: unaryfunc
    nb_bool: inquiry
    nb_invert: unaryfunc
    nb_lshift: binaryfunc
    nb_rshift: binaryfunc
    nb_and: binaryfunc
    nb_xor: binaryfunc
    nb_or: binaryfunc
    nb_int: unaryfunc
    nb_reserved: c_void_p  # formerly nb_long
    nb_float: unaryfunc

    nb_inplace_add: binaryfunc
    nb_inplace_subtract: binaryfunc
    nb_inplace_multiply: binaryfunc
    nb_inplace_remainder: binaryfunc
    nb_inplace_power: ternaryfunc
    nb_inplace_lshift: binaryfunc
    nb_inplace_rshift: binaryfunc
    nb_inplace_and: binaryfunc
    nb_inplace_xor: binaryfunc
    nb_inplace_or: binaryfunc

    nb_floor_divide: binaryfunc
    nb_true_divide: binaryfunc
    nb_inplace_floor_divide: binaryfunc
    nb_inplace_true_divide: binaryfunc

    nb_index: unaryfunc

    nb_matrix_multiply: binaryfunc
    nb_inplace_matrix_multiply: binaryfunc


@struct
class PyMappingMethods(Structure):
    mp_length: lenfunc
    mp_subscript: binaryfunc
    mp_ass_subscript: objobjargproc


@struct
class PySequenceMethods(Structure):
    sq_length: lenfunc
    sq_concat: binaryfunc
    sq_repeat: ssizeargfunc
    sq_item: ssizeargfunc
    was_sq_slice: c_void_p
    sq_ass_item: ssizeobjargproc
    was_sq_ass_slice: c_void_p
    sq_contains: objobjproc
    sq_inplace_concat: binaryfunc
    sq_inplace_repeat: ssizeargfunc
