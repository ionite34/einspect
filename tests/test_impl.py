"""Tests for the @impl decorator and orig proxy."""
from __future__ import annotations

from contextlib import ExitStack

import pytest

from einspect import impl, orig, view


def test_impl_error():
    with pytest.raises(TypeError, match="cls must be a type"):
        # noinspection PyTypeChecker
        @impl(1)
        def _foo_fn(self):
            pass


def test_impl_new_func():
    with ExitStack() as stack:

        @impl(int, detach=True)
        def _foo_fn(self, x):
            return str(self + x)

        stack.callback(_foo_fn._impl_finalize)

        # noinspection PyUnresolvedReferences
        assert (10)._foo_fn(5) == "15"


def test_impl_new_property():
    UserStr = type("UserStr", (str,), {})

    @impl(UserStr, detach=True)
    @property
    def as_str(self) -> str:
        return str(self)

    # noinspection PyUnresolvedReferences
    assert UserStr("abc").as_str == "abc"


def test_impl_func():
    # Implement a new method for int
    @impl(int)
    def __matmul__(self, other):
        return self * other

    assert hasattr(int, "__matmul__")

    a = 4
    b = 10
    # noinspection PyUnresolvedReferences
    assert a @ b == 40

    # Restore original (this deletes our implementation)
    view(int).restore("__matmul__")
    # check int no longer has __matmul__
    assert not hasattr(int, "__matmul__")
    # using the operator should error
    with pytest.raises(TypeError):
        # noinspection PyUnresolvedReferences
        assert not a @ b


def test_impl_property():
    _call = None

    @impl(int, detach=True)
    @property
    def real(self):
        nonlocal _call
        _call = self
        return orig(int).real.__get__(self)

    assert int.real is real

    assert (123).real == 123
    assert _call == 123

    assert (456).real == 456
    assert _call == 456

    # Restore original
    view(int).restore("real")
    assert int.real is not real
