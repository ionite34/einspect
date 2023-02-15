"""Test moving of views."""
from ast import literal_eval

import pytest

from einspect import view
from einspect.errors import UnsafeError


def test_move_err():
    v = view(123)
    with pytest.raises(TypeError), v.unsafe():
        v.move_to("not a view")  # type: ignore


@pytest.mark.run_in_subprocess
def test_move_op():
    a = literal_eval("'eed25194-bb5e-4c96'")
    b = literal_eval("'90d584f0-2b6e-449c'")
    v = view(a)
    v <<= b
    assert a == b


@pytest.mark.run_in_subprocess
def test_move_from():
    a = literal_eval("'1121e2bf-2078-427f'")
    b = literal_eval("'704ffc52-f6dd-4ed6'")
    v = view(a)
    v.move_from(view(b))
    assert a == b


@pytest.mark.run_in_subprocess
def test_move_instance_dicts():
    """Move between objects with instance dicts."""
    Foo = type("Num", (tuple,), {})
    Bar = type("Num", (tuple,), {})

    x = Foo((1, 2, 3))
    y = Bar((4, 5, 6))

    view(x) << view(y)
    assert x == (4, 5, 6)
    assert x.__dict__ is y.__dict__


@pytest.mark.run_in_subprocess
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
    ls = ["f6dd", "4ed6"]
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


@pytest.mark.run_in_subprocess
def test_swap():
    a = literal_eval("'78950fa2-93a4-4ac4'")
    b = literal_eval("'236ad434-c134-4f75'")
    view(a).swap(b)

    assert a == "236ad434-c134-4f75"
    assert b == "78950fa2-93a4-4ac4"


@pytest.mark.run_in_subprocess
def test_swap_dict():
    # Classes with instance dicts should also be swapped
    A = type("A", (int,), {})
    a = A(500)
    a.foo = "foo"

    B = type("B", (int,), {})
    b = B(700)
    b.bar = "bar"

    view(a).swap(b)

    assert a == 700
    assert a.bar == "bar"
    assert not hasattr(a, "foo")

    assert b == 500
    assert b.foo == "foo"
    assert not hasattr(b, "bar")
