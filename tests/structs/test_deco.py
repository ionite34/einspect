from ctypes import Structure, c_void_p

from einspect.structs.deco import struct


def test_struct_deco():
    @struct
    class Foo(Structure):
        x: int
        y: int

    assert Foo.x.offset == 0
    assert Foo.y.offset == 8

    f = Foo()
    assert f.x == 0
    assert f.y == 0


def test_struct_deco_factory():
    @struct(
        fields=[
            ("x", c_void_p),
        ]
    )
    class Foo(Structure):
        x: int
        y: int

    f = Foo()
    assert f.x is None
    assert f.y == 0
