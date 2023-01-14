"""Tests for the @impl decorator and orig proxy."""
from __future__ import annotations

import pytest

from einspect import impl, orig


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
