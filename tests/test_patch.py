from ctypes import POINTER, c_void_p

from einspect._patch import _Null_LP_PyObject


def test_null_lp_repr() -> None:
    obj = _Null_LP_PyObject()
    assert repr(obj).startswith("<NULL ptr[PyObject] at")


def test_null_lp_eq() -> None:
    obj = _Null_LP_PyObject()
    other_null_ptr = POINTER(c_void_p)()
    assert obj is not other_null_ptr
    assert obj == other_null_ptr
    assert obj != "other"
