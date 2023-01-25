import ctypes
from ctypes import POINTER, c_uint32, c_void_p

import pytest

from einspect.structs import PyObject
from einspect.types import NULL, ptr


def test_ptr() -> None:
    p = ptr[ctypes.c_void_p]
    assert p == ctypes.POINTER(ctypes.c_void_p)

    # TypeError if wrong type
    with pytest.raises(TypeError):
        _ = ptr[123]


@pytest.mark.parametrize(
    "ptr_obj",
    [
        POINTER(PyObject)(),
        POINTER(c_void_p)(),
        POINTER(c_uint32)(),
    ],
)
def test_null_eq(ptr_obj) -> None:
    """Test NULL singleton."""
    # Should be equal to other NULL pointers
    assert NULL is not ptr_obj
    assert NULL == ptr_obj


@pytest.mark.parametrize(
    "ptr_obj",
    [
        POINTER(c_void_p)(c_void_p(123)),
        PyObject.from_object(123).as_ref(),
    ],
)
def test_null_not_eq(ptr_obj) -> None:
    """Test NULL singleton."""
    # Should not be equal to other non-NULL pointers
    assert NULL != ptr_obj
