import pytest

from einspect.type_orig import _cache, add_cache, get_cache, in_cache, orig


def test_orig() -> None:
    obj = orig(str)
    # repr
    assert repr(obj) == "orig(str)"
    # call
    assert obj("abc") == "abc"
    # dunder
    assert getattr(obj, "_orig__type") is str


def test_orig_weak_key() -> None:
    class Foo:
        def abc(self):
            pass

    add_cache(Foo, "abc", Foo.abc)
    assert in_cache(Foo, "abc")

    # Delete Foo now, should be removed from cache
    del Foo

    print(dict(_cache))
    assert not _cache


def test_orig_cache() -> None:
    # First access will cache methods
    assert orig(str).upper("abc") == "ABC"
    # check in _slots_cache
    assert _cache[str]["upper"] == str.upper
    assert in_cache(str, "upper")
    assert get_cache(str, "upper") == str.upper
    # check in orig
    assert orig(str).upper("abc") == "ABC"
