from ctypes import POINTER, Structure, c_uint32, c_void_p
from typing import Optional, Union

import pytest

from einspect.protocols import bind_api
from einspect.structs.deco import struct


def test_struct() -> None:
    @struct
    class Foo(Structure):
        x: POINTER(c_void_p)

    assert Foo.x


def test_struct_pointer_error() -> None:
    with pytest.raises(TypeError):

        @struct
        class Foo(Structure):
            x: POINTER(str)  # type: ignore

        assert not Foo


def test_struct_union() -> None:
    @struct
    class Foo(Structure):
        x: Union[POINTER(c_void_p), POINTER(c_uint32)]

    assert Foo.x.offset == 0


def test_api_bind() -> None:
    class Foo(Structure):
        @bind_api(lambda: 0)
        def func(self) -> Optional[int]: ...

    assert Foo.func() == 0
