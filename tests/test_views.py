import ctypes
import gc

import pytest

from einspect import structs, errors
from einspect.views import view, View, ListView, IntView, TupleView


class TestView:
    def test_type(self):
        obj = object()
        v = view(obj)
        assert isinstance(v, View)
        assert isinstance(v._pyobject, structs.PyObject)

    def test_ref(self):
        obj = object()
        v = view(obj, ref=True)
        # Should be 2 references,
        # 1. "obj", 2. "v" (with ref=True)
        assert v.ref_count == 2

    def test_no_ref(self):
        obj = object()
        v = view(obj, ref=False)
        assert v.ref_count == 1

    def test_base_ref(self):
        """Access base with reference."""
        obj = object()
        v = view(obj, ref=True)
        assert isinstance(v.base, ctypes.py_object)
        assert v.base.value is obj

    def test_base_weakref(self):
        """Access base after weakref is deleted."""

        class A:
            pass

        obj = A()
        v = view(obj, ref=False)
        del obj
        with pytest.raises(errors.MovedError):
            _ = v.base

    def test_base_no_ref(self):
        """Access base with no ref should require unsafe."""
        obj = object()
        v = view(obj, ref=False)
        with pytest.raises(errors.UnsafeError):
            _ = v.base

    def test_base_unsafe(self):
        """Access base with unsafe."""
        obj = object()
        v = view(obj, ref=False)

        with v.unsafe():
            assert v.ref_count == 1
            assert v.base.value is obj


class TestListView:
    def test_new(self):
        ls = [1, 2, 3]
        v = view(ls)
        assert isinstance(v, ListView)
        assert isinstance(v._pyobject, structs.PyListObject)
        assert v.size == 3
        assert v.type == list


class TestIntView:
    @pytest.mark.parametrize(["obj", "size"], [
        (1, 1),
        (2 ** 8, 1),
        (0, 0),  # CPython detail where 0 has ob_size of 0
        (-1, -1),
        (-9000, -1),
    ])
    def test_new(self, obj, size):
        v = view(obj)
        assert isinstance(v, IntView)
        assert isinstance(v._pyobject, structs.PyLongObject)
        assert v.type == int
        assert v.size == size
        assert v.value == obj


class TestTupleView:
    def test_new(self):
        tup = ("dog", "cat")
        v = view(tup)
        assert isinstance(v, TupleView)
        assert isinstance(v._pyobject, structs.PyTupleObject)
        assert v.size == 2
        assert v.type == tuple
