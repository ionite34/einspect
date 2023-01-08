import ctypes

import pytest

from einspect import structs, errors, view
from einspect.views.view_base import View


class TestView:
    def test_type(self):
        obj = object()
        v = view(obj)
        assert isinstance(v, View)
        assert isinstance(v._pyobject, structs.PyObject)

    def test_ref(self):
        obj = object()
        v = View(obj, ref=True)
        # Should be 2 references,
        # 1. "obj", 2. "v" (with ref=True)
        assert v.ref_count == 2

    def test_no_ref(self):
        obj = object()
        v = View(obj, ref=False)
        assert v.ref_count == 1

    def test_base_ref(self):
        """Access base with reference."""
        obj = object()
        v = View(obj, ref=True)
        assert isinstance(v.base, ctypes.py_object)
        assert v.base.value is obj

    def test_base_weakref(self):
        """Access base after weakref is deleted."""

        class A:
            pass

        obj = A()
        v = View(obj, ref=False)
        del obj
        with pytest.raises(errors.MovedError):
            _ = v.base

    def test_base_no_ref(self):
        """Access base with no ref should require unsafe."""
        obj = object()
        v = View(obj, ref=False)
        with pytest.raises(errors.UnsafeError):
            _ = v.base

    def test_base_unsafe(self):
        """Access base with unsafe."""
        obj = object()
        v = View(obj, ref=False)
        assert v.ref_count == 1

        with v.unsafe():
            assert v.base.value is obj

    def test_drop(self):
        """Test accessing after drop."""
        obj = object()
        v = View(obj, ref=True)
        assert v.base.value is obj
        v.drop()
        with pytest.raises(errors.DroppedReferenceError):
            _ = v.base.value


