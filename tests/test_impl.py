"""Tests for the @impl decorator and orig proxy."""
from __future__ import annotations

import pytest

from einspect import impl, orig, view


def test_impl_new_func():
    @impl(int)
    def _foo_fn(self, x: int) -> str:
        return str(self + x)

    # noinspection PyUnresolvedReferences
    assert (10)._foo_fn(5) == "15"


def test_impl_cache():
    @impl(int)
    def _foo_fn(self, x: int) -> str:
        return str(self + x)

    impl(int)(_foo_fn)

    # noinspection PyUnresolvedReferences
    assert (10)._foo_fn(5) == "15"


def test_impl_new_property():
    @impl(int)
    @property
    def _custom_as_str(self) -> str:
        return orig(int).__str__(self)

    # noinspection PyUnresolvedReferences
    assert (10)._custom_as_str == "10"


# noinspection PyUnresolvedReferences
def test_impl_new_slot():
    UserType = type("UserType", (object,), {})
    obj = UserType()

    @impl(UserType)
    def __getitem__(self, item) -> str:
        return item

    assert obj[0] == 0
    assert obj[1] == 1


def test_impl_error():
    with pytest.raises(TypeError, match="cls must be a type"):
        # noinspection PyTypeChecker
        @impl(1)
        def _foo_fn(self):
            pass


@pytest.mark.run_in_subprocess
def test_impl_func():
    # Implement an override for list __add__
    @impl(list)
    def __add__(self, other):
        return ["test-123"]

    a = [1, 2]
    b = [3, 4]
    assert a + b == ["test-123"]


@pytest.mark.run_in_subprocess
def test_impl_func_2():
    # Implement a new method for int
    @impl(int)
    def __matmul__(self, other):
        return self // other

    a = 100
    b = 4
    # noinspection PyUnresolvedReferences
    assert a @ b == 25


def test_impl_property():
    _call = None

    @impl(int)
    @property
    def real(self):
        nonlocal _call
        _call = self
        return orig(int).real.__get__(self)

    assert (123).real == 123
    assert _call == 123

    assert (456).real == 456
    assert _call == 456


def test_impl_new():
    _call = None

    @impl(object)
    def __new__(cls, *args, **kwargs):
        nonlocal _call
        _call = (cls, args, kwargs)
        return orig(cls).__new__(cls, *args, **kwargs)

    # Test normal object creation
    _ = object()
    assert _call == (object, (), {})

    # Test subclass
    class Foo:
        def __init__(self, a, b, kwd=None):
            self.args = (a, b)
            self.kwd = kwd

    obj = Foo(1, 2, kwd="hi")
    assert isinstance(obj, Foo)
    assert _call == (Foo, (1, 2), {"kwd": "hi"})
