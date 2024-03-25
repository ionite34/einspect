"""Test unsafe context and operations."""

import pytest

from einspect import errors, unsafe, view


def test_unsafe_error() -> None:
    v = view(1)
    with pytest.raises(errors.UnsafeError):
        v.ref_count += 1


def test_global_unsafe() -> None:
    v = view(1)
    assert not v._unsafe
    assert not v._local_unsafe
    with unsafe():
        assert v._unsafe
        assert not v._local_unsafe
    assert not v._unsafe
    assert not v._local_unsafe


@pytest.mark.run_in_subprocess
def test_change_type():
    x = 2**28 + 5
    v = view(x)
    assert v.type is int
    with v.unsafe() as v:
        v.type = bool
        assert isinstance(x, bool)
        assert x - 5 == 2**28
        v.type = int
        assert isinstance(x, int)
