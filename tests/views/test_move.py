"""Test moving of views."""
from ast import literal_eval

import pytest

from einspect import view
from einspect.errors import UnsafeError


def test_move_err(new_int: int):
    v = view(new_int)
    with pytest.raises(TypeError), v.unsafe():
        v.move_to("not a view")  # type: ignore


def test_move_op(new_int: int):
    v = view(new_int)
    v <<= 5
    assert new_int == 5
    assert id(new_int) != id(5)


def test_move_from(new_int: int):
    v = view(new_int)
    v.move_from(view(5))
    assert new_int == 5
    assert id(new_int) != id(5)


def test_move_instance_dicts():
    """Move between objects with instance dicts."""
    Foo = type("Num", (tuple,), {})
    Bar = type("Num", (tuple,), {})

    x = Foo((1, 2, 3))
    y = Bar((4, 5, 6))

    view(x) << view(y)
    assert x == (4, 5, 6)
    assert x.__dict__ is y.__dict__


def test_move_str():
    """Move between strs."""
    a = literal_eval("'abcdef'")
    b = literal_eval("'xyz'")
    assert a == "abcdef"
    assert hash(a) == hash("abcdef")
    view(a) << view(b)
    assert a == "xyz"
    assert hash(a) == hash("xyz")


def test_move_unsafe_size():
    """Unsafe move due to size."""
    v = view(5)
    with pytest.raises(UnsafeError, match="out of bounds"):
        v <<= 2**90


def test_move_unsafe_gc_types():
    """Unsafe move due to non-gc type into gc type."""
    ls = [1, 2, 3]
    v = view(ls)
    with pytest.raises(UnsafeError, match="gc type"):
        v <<= 10


def test_move_unsafe_instance_dict():
    """Unsafe move due to instance dict."""

    class Num(int):
        pass

    v = view(900)
    with pytest.raises(UnsafeError, match="instance dict"):
        v <<= Num()


def test_swap():
    a = literal_eval("'78950fa2-93a4-4ac4'")
    b = literal_eval("'236ad434-c134-4f75'")
    view(a).swap(b)

    assert a == "236ad434-c134-4f75"
    assert b == "78950fa2-93a4-4ac4"


def test_swap_dict():
    # Classes with instance dicts should also be swapped
    A = type("A", (str,), {})
    x = A(literal_eval("'A-bca9f33a-9123'"))
    x.foo = "123"

    B = type("B", (str,), {})
    y = B(literal_eval("'B-08b35581-cd6a'"))
    y.bar = "321"

    view(x).swap(y)

    assert y == "A-bca9f33a-9123"
    assert y.foo == "123"
    assert not hasattr(y, "bar")

    assert x == "B-08b35581-cd6a"
    assert x.bar == "321"
    assert not hasattr(x, "foo")
