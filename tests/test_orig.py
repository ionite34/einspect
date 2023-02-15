import pytest

from einspect.type_orig import (
    _cache,
    get_cache,
    get_type_cache,
    in_cache,
    orig,
    try_cache_attr,
)


def test_orig() -> None:
    obj = orig(str)
    # repr
    assert repr(obj) == "orig(str)"
    # call
    assert obj("abc") == "abc"
    # dunder
    assert getattr(obj, "_orig__type") is str


def test_orig_cache() -> None:
    # First access will cache methods
    assert orig(str).upper("abc") == "ABC"
    # check in _slots_cache
    assert _cache[str]["upper"] == str.upper
    assert in_cache(str, "upper")
    assert get_cache(str, "upper") == str.upper
    # check in orig
    assert orig(str).upper("abc") == "ABC"


def test_get_type_cache() -> None:
    class A:
        pass

    # Initially should not be in cache
    with pytest.raises(KeyError):
        get_type_cache(A)

    # Add to cache
    A.abc = 123
    try_cache_attr(A, "abc")

    assert get_type_cache(A) == {"abc": 123}
