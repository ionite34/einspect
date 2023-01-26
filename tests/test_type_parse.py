from ctypes import POINTER, c_uint32, c_void_p
from typing import Union

import pytest

from einspect.structs.deco import struct


def test_struct() -> None:
    @struct
    class Foo:
        x: POINTER(c_void_p)

    assert Foo


def test_struct_pointer_error() -> None:
    with pytest.raises(TypeError):

        @struct
        class Foo:
            x: POINTER(str)  # type: ignore

        assert not Foo


def test_struct_union():
    @struct
    class Foo:
        x: Union[POINTER(c_void_p), POINTER(c_uint32)]

    assert Foo.x._type_ == c_void_p
