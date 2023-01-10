"""https://github.com/python/cpython/blob/3.11/Include/object.h"""
from __future__ import annotations

from ctypes import PYFUNCTYPE, Structure, c_char_p, c_int, c_void_p, py_object
from enum import IntEnum

from einspect.api import Py_ssize_t
from einspect.structs.deco import struct
from einspect.structs.include.pybuffer_h import getbufferproc, releasebufferproc
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
    "PySendResult",
    "TpFlags",
    "PyBufferProcs",
    "PyAsyncMethods",
    "PyNumberMethods",
    "PyMappingMethods",
    "PySequenceMethods",
)

# Function types
# https://github.com/python/cpython/blob/3.11/Include/object.h#L196-L227
unaryfunc = PYFUNCTYPE(py_object, py_object)
binaryfunc = PYFUNCTYPE(py_object, py_object, py_object)
ternaryfunc = PYFUNCTYPE(py_object, py_object, py_object, py_object)
inquiry = PYFUNCTYPE(c_int, py_object)
lenfunc = PYFUNCTYPE(Py_ssize_t, py_object)
ssizeargfunc = PYFUNCTYPE(py_object, py_object, Py_ssize_t)
ssizessizeargfunc = PYFUNCTYPE(py_object, py_object, Py_ssize_t, Py_ssize_t)
ssizeobjargproc = PYFUNCTYPE(c_int, py_object, Py_ssize_t, py_object)
ssizessizeobjargproc = PYFUNCTYPE(c_int, py_object, Py_ssize_t, Py_ssize_t, py_object)
objobjargproc = PYFUNCTYPE(c_int, py_object, py_object, py_object)

objobjproc = PYFUNCTYPE(c_int, py_object, py_object)
visitproc = PYFUNCTYPE(c_int, py_object, c_void_p)
traverseproc = PYFUNCTYPE(c_int, py_object, visitproc, c_void_p)

freefunc = PYFUNCTYPE(None, c_void_p)
destructor = PYFUNCTYPE(None, py_object)
getattrfunc = PYFUNCTYPE(py_object, py_object, c_char_p)
getattrofunc = PYFUNCTYPE(py_object, py_object, py_object)
setattrfunc = PYFUNCTYPE(c_int, py_object, c_char_p, py_object)
setattrofunc = PYFUNCTYPE(c_int, py_object, py_object, py_object)
reprfunc = PYFUNCTYPE(py_object, py_object)
hashfunc = PYFUNCTYPE(Py_ssize_t, py_object)
richcmpfunc = PYFUNCTYPE(py_object, py_object, py_object, c_int)
getiterfunc = PYFUNCTYPE(py_object, py_object)
iternextfunc = PYFUNCTYPE(py_object, py_object)

descrgetfunc = PYFUNCTYPE(py_object, py_object, py_object, py_object)
descrsetfunc = PYFUNCTYPE(c_int, py_object, py_object, py_object)
initproc = PYFUNCTYPE(c_int, py_object, py_object, py_object)
newfunc = PYFUNCTYPE(py_object, py_object, py_object, py_object)
allocfunc = PYFUNCTYPE(py_object, py_object, Py_ssize_t)

# PyObject *(*vectorcallfunc)(PyObject *callable, PyObject *const *args, size_t nargsf, PyObject *kwnames)
vectorcallfunc = PYFUNCTYPE(py_object, py_object, ptr[py_object], Py_ssize_t, py_object)
# PySendResult (*sendfunc)(PyObject *iter, PyObject *value, PyObject **result)
sendfunc = PYFUNCTYPE(c_int, py_object, py_object, ptr[py_object])


class PySendResult(IntEnum):
    """Result of calling PyIter_Send."""

    PYGEN_RETURN = 0
    PYGEN_ERROR = -1
    PYGEN_NEXT = 1


class TpFlags(IntEnum):
    """
    Type flags (tp_flags)

    https://github.com/python/cpython/blob/3.11/Include/object.h#L350-L440
    """

    STATIC_BUILTIN = 1 << 1
    MANAGED_WEAKREF = 1 << 3
    MANAGED_DICT = 1 << 4
    PREHEADER = MANAGED_WEAKREF | MANAGED_DICT
    # Set if instances of the type object are treated as sequences for pattern matching
    SEQUENCE = 1 << 5
    # Set if instances of the type object are treated as mappings for pattern matching
    MAPPING = 1 << 6
    # Disallow creating instances of the type: set tp_new to NULL and don't create
    # the "__new__" key in the type dictionary.
    DISALLOW_INSTANTIATION = 1 << 7
    # Set if the type object is immutable: type attributes cannot be set nor deleted
    IMMUTABLETYPE = 1 << 8
    # Set if the type object is dynamically allocated
    HEAPTYPE = 1 << 9
    # Set if the type allows subclassing
    BASETYPE = 1 << 10
    # Set if the type implements the vectorcall protocol (PEP 590)
    HAVE_VECTORCALL = 1 << 11
    # Set if the type is 'ready' -- fully initialized
    READY = 1 << 12
    # Set while the type is being 'readied', to prevent recursive ready calls
    READYING = 1 << 13
    # Objects support garbage collection (see objimpl.h)
    HAVE_GC = 1 << 14
    # These two bits are preserved for Stackless Python, next after this is 17
    HAVE_STACKLESS_EXTENSION = 0  # if STACKLESS (3 << 15)
    # Objects behave like an unbound method
    METHOD_DESCRIPTOR = 1 << 17
    # Object has up-to-date type attribute cache
    VALID_VERSION_TAG = 1 << 19
    # Type is abstract and cannot be instantiated
    IS_ABSTRACT = 1 << 20
    # This undocumented flag gives certain built-ins their unique pattern-matching
    # behavior, which allows a single positional subpattern to match against the
    # subject itself (rather than a mapped attribute on it):
    MATCH_SELF = 1 << 22
    # These flags are used to determine if a type is a subclass.
    LONG_SUBCLASS = 1 << 24
    LIST_SUBCLASS = 1 << 25
    TUPLE_SUBCLASS = 1 << 26
    BYTES_SUBCLASS = 1 << 27
    UNICODE_SUBCLASS = 1 << 28
    DICT_SUBCLASS = 1 << 29
    BASE_EXC_SUBCLASS = 1 << 30
    TYPE_SUBCLASS = 1 << 31
    DEFAULT = HAVE_STACKLESS_EXTENSION | 0
    # Some of these flags reuse lower bits (removed as part of the Python 3.0 transition).
    HAVE_FINALIZE = 1 << 0
    HAVE_VERSION_TAG = 1 << 18


@struct
class PyAsyncMethods(Structure):
    am_await: unaryfunc
    am_aiter: unaryfunc
    am_anext: unaryfunc
    am_send: sendfunc


@struct
class PyBufferProcs(Structure):
    bf_getbuffer: getbufferproc
    bf_releasebuffer: releasebufferproc


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
