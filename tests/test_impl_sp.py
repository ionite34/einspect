"""(Subprocess) Tests for the @impl decorator and orig proxy."""
from __future__ import annotations

import pytest

from einspect import impl, orig, view


@pytest.mark.run_in_subprocess
def test_impl_restore():
    @impl(int)
    def __repr__(self):
        return "repr"

    @impl(int)
    def x(self):
        return "x"

    n = 5
    assert repr(n) == "repr"
    # noinspection PyUnresolvedReferences
    assert n.x() == "x"

    view(int).restore()

    assert repr(n) == "5"
    with pytest.raises(AttributeError):
        # noinspection PyUnresolvedReferences
        _ = n.x()


@pytest.mark.run_in_subprocess
def test_impl_new_func_finalize():
    # Test that finalizer works, deleting function should remove the impl
    @impl(int, detach=True)
    def _test_final(self):
        return str(self)

    _test_final._impl_finalize()

    with pytest.raises(AttributeError, match="has no attribute '_test_final'"):
        # noinspection PyUnresolvedReferences
        _ = (10)._test_final()

    assert not hasattr(int, "_test_final")


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


@pytest.mark.run_in_subprocess
def test_impl_new():
    _call = None

    @impl(object)
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


# noinspection PyUnresolvedReferences
@pytest.mark.run_in_subprocess
def test_impl_object():
    @impl(object)
    def __matmul__(self, other):
        return self.__class__.__name__ + str(other)

    assert object() @ 1 == "object1"
    assert int() @ 10 == "int10"

    # Restore original
    view(object).restore("__matmul__")
    with pytest.raises(TypeError):
        _ = object()[3]
