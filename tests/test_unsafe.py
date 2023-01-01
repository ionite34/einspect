"""Test unsafe context and operations."""
import pytest

from einspect import view, errors


def test_unsafe_error():
    v = view(1)
    current = v.ref_count
    with pytest.raises(errors.UnsafeError):
        v.ref_count = 0
    # setter should not have run
    assert v.ref_count == current
