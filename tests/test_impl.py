"""Tests for the @impl decorator and orig proxy."""
from __future__ import annotations

import pytest

from einspect import impl, orig


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


@pytest.mark.run_in_subprocess
def test_impl_func():
    # Implement an override for list __add__
    @impl(list)
    def __add__(self, other):
        return "test-123"

    a = [1, 2]
    b = [3, 4]
    assert a + b == "test-123"

    # Implement a new method for set
    @impl(set)
    def __matmul__(self, other):
        return self | other

    a = {1, 2}
    b = {3, 4}
    # noinspection PyUnresolvedReferences
    assert a @ b == {1, 2, 3, 4}


@pytest.mark.run_in_subprocess
def test_impl_property():
    # Implement an override property for int
    @impl(int)
    @property
    def real(self):
        return orig(int).real.__get__(self) + 10

    assert (0).real == 10
    assert (5).real == 15
