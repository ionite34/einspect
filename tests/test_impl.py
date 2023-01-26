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


@pytest.mark.run_in_subprocess
def test_impl_property():
    # Implement an override property for int
    @impl(int)
    @property
    def real(self):
        return orig(int).real.__get__(self) + 10

    assert (0).real == 10
    assert (5).real == 15
