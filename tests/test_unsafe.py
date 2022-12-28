"""Test unsafe context and operations."""
import pytest

from einspect import view, errors


def test_unsafe_error():
    x = "hello"
    v = view(x)
    current = v.hash
    with pytest.raises(errors.UnsafeError):
        v.hash = 500
    # setter should not have run
    assert v.hash == current


def test_tuple_set_item():
    t = (1, 2, 3)
    v = view(t)
    with v.unsafe():
        v[1] = 4
        v[2] = 5
    assert t == (1, 4, 5)
