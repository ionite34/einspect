import ctypes

import pytest

from einspect.types import ptr


def test_ptr() -> None:
    p = ptr[ctypes.c_void_p]
    assert p == ctypes.POINTER(ctypes.c_void_p)

    # TypeError if wrong type
    with pytest.raises(TypeError):
        _ = ptr[123]
