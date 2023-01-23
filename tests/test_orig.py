import pytest

from einspect.type_orig import _slots_cache, get_cache, in_cache, orig


def test_orig() -> None:
    obj = orig(str)
    # repr
    assert repr(obj) == "orig(str)"
    # call
    assert obj("abc") == "abc"
    # dunder
    assert getattr(obj, "_orig__type") is str


def test_orig_cache() -> None:
    # Initial not in cache
    assert str not in _slots_cache
    assert not in_cache(str, "upper")
    # First access will cache methods
    assert orig(str).upper("abc") == "ABC"
    # check in _slots_cache
    assert _slots_cache[str]["upper"] == str.upper
    assert get_cache(str, "upper") == str.upper
    # check in orig
    assert orig(str).upper("abc") == "ABC"
