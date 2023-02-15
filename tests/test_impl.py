"""Tests for the @impl decorator and orig proxy."""
from __future__ import annotations

from contextlib import ExitStack

import pytest

from einspect import impl, orig, view


def test_impl_new_func():
    with ExitStack() as stack:

        @impl(int, detach=True)
        def _foo_fn(self, x):
            return str(self + x)

        stack.callback(_foo_fn._impl_finalize)

        # noinspection PyUnresolvedReferences
        assert (10)._foo_fn(5) == "15"


@pytest.mark.run_in_subprocess
def test_impl_new_func_finalize():
    # Test that finalizer works, deleting function should remove the impl
    with ExitStack() as stack:

        @impl(int, detach=True)
        def _test_final(self):
            return str(self)

        stack.callback(_test_final._impl_finalize)

        _test_final._impl_finalize()

        with pytest.raises(AttributeError, match="has no attribute '_test_final'"):
            # noinspection PyUnresolvedReferences
            _ = (10)._test_final()


@pytest.mark.run_in_subprocess
def test_impl_cache():
    # Test that impls are cached
    @impl(int)
    def _foo_fn(self, x: int) -> str:
        return str(self + x)

    impl(int)(_foo_fn)

    # noinspection PyUnresolvedReferences
    assert (10)._foo_fn(5) == "15"

    # Restore original
    view(int).restore("_foo_fn")


def test_impl_new_property():
    UserStr = type("UserStr", (str,), {})

    @impl(UserStr, detach=True)
    @property
    def _custom_as_str(self) -> str:
        return orig(UserStr).__str__(self)

    # noinspection PyUnresolvedReferences
    assert UserStr("abc")._custom_as_str == "abc"


# noinspection PyUnresolvedReferences
@pytest.mark.run_in_subprocess
def test_impl_new_slot():
    UserType = type("UserType", (object,), {})
    obj = UserType()

    @impl(UserType)
    def __getitem__(self, item) -> str:
        return item

    assert obj[0] == 0
    assert obj[1] == 1


@pytest.mark.run_in_subprocess
def test_impl_error():
    with pytest.raises(TypeError, match="cls must be a type"):
        # noinspection PyTypeChecker
        @impl(1)
        def _foo_fn(self):
            pass


def test_impl_func():
    # Implement a new method for int
    @impl(int)
    def __matmul__(self, other):
        return self * other

    a = 4
    b = 10
    # noinspection PyUnresolvedReferences
    assert a @ b == 40

    view(int).restore("__matmul__")


def test_impl_property():
    _call = None

    @impl(int, detach=True)
    @property
    def real(self):
        nonlocal _call
        _call = self
        return orig(int).real.__get__(self)

    assert (123).real == 123
    assert _call == 123

    assert (456).real == 456
    assert _call == 456


def test_impl_new():
    _call = None

    @impl(object, detach=True)
    def __new__(cls, *args, **kwargs):
        nonlocal _call
        _call = (cls, args, kwargs)
        return orig(cls).__new__(cls, *args, **kwargs)

    # Test normal object creation
    _ = object()
    assert _call == (object, (), {})

    # Test subclass
    class Foo:
        def __init__(self, a, b, kwd=None):
            self.args = (a, b)
            self.kwd = kwd

    obj = Foo(1, 2, kwd="hi")
    assert isinstance(obj, Foo)
    assert _call == (Foo, (1, 2), {"kwd": "hi"})


@pytest.mark.run_in_subprocess
def test_impl_detach_weakref():
    # impl detach should require methods to be weakrefable
    class SomeClass:
        pass

    class Func:
        __slots__ = ("_func",)
        __name__ = "Func"

        def __call__(self, *args, **kwargs):
            pass

    fn = Func()

    with pytest.raises(TypeError, match="support weakrefs"):
        # noinspection PyTypeChecker
        impl(SomeClass, detach=True)(fn)

    # With detach=False, it should work
    res = impl(SomeClass, detach=False)(fn)
    assert res is fn


@pytest.mark.run_in_subprocess
def test_impl_type():
    # Test that impl works on types
    @impl(type)
    def __matmul__(self, other):
        return self, other

    # stack.callback(__matmul__._impl_finalize)

    # noinspection PyUnresolvedReferences
    assert str @ 123 == (str, 123)

    # Should also work for custom types
    class Foo:
        pass

    # noinspection PyUnresolvedReferences
    assert Foo @ "hi" == (Foo, "hi")
