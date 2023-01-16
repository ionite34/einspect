from ctypes import POINTER, c_void_p

import pytest

from einspect.structs.deco import struct


def test_struct():
    @struct
    class Foo:
        x: POINTER(c_void_p)

    assert Foo


def test_struct_pointer_error():
    with pytest.raises(TypeError):

        @struct
        class Foo:
            x: POINTER(str)  # type: ignore

        assert not Foo
