"""Test unsafe context and operations."""
from ctypes import POINTER, c_int, pointer

import pytest

from einspect import errors, view


def test_unsafe_error():
    v = view(1)
    with pytest.raises(errors.UnsafeError):
        v.ref_count = 0


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
