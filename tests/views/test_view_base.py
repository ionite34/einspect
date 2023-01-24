import gc

import pytest

from einspect import errors, structs, view
from einspect.views.view_base import AnyView, VarView, View


class TestView:
    view_type = View
    obj_type = object

    def get_obj(self):
        return self.obj_type()

    def check_ref(self, a, b):
        # Skip builtin types
        if self.obj_type.__module__ == "builtins":
            return
        # Check ref count unless we're an instance of int or singletons
        if self.obj_type in (int, bool, type(None)):
            return
        assert a == b

    def test_type(self):
        obj = self.get_obj()
        v = self.view_type(obj)
        assert isinstance(v, View)
        assert isinstance(v._pyobject, structs.PyObject)
        assert v.type == type(obj)

    def test_factory(self):
        """Test factory."""
        obj = self.get_obj()
        v = view(obj)  # type: ignore
        assert type(v) is self.view_type

    def test_size(self):
        # For sized test subclasses
        obj = self.get_obj()
        v = self.view_type(obj)
        st = v._pyobject
        if hasattr(st, "ob_size") or issubclass(self.view_type, VarView):
            assert v.size == st.ob_size  # type: ignore

    def test_ref(self):
        obj = self.get_obj()
        v = self.view_type(obj, ref=True)
        # Should be 2 references,
        # 1. "obj", 2. "v" (with ref=True)
        self.check_ref(v.ref_count, 2)

    def test_no_ref(self):
        obj = self.get_obj()
        v = self.view_type(obj, ref=False)
        self.check_ref(v.ref_count, 1)

    def test_base_ref(self):
        """Access base with reference."""
        obj = self.get_obj()
        v = self.view_type(obj, ref=True)
        assert v.base is obj

    def test_base_no_ref(self):
        """Access base with no ref should require unsafe."""
        obj = self.get_obj()
        v = self.view_type(obj, ref=False)
        # Normal case (no weakref support)
        if self.obj_type.__weakrefoffset__ == 0:
            with pytest.raises(errors.UnsafeError):
                assert not v.base
        # Alternate if supports weakref
        else:
            # Check weakref exists
            assert v._base_weakref is not None
            assert v._base_weakref() is obj
            assert v.base is obj

    def test_base_unsafe(self):
        """Access base with unsafe."""
        obj = self.get_obj()
        v = self.view_type(obj, ref=False)
        self.check_ref(v.ref_count, 1)

        with v.unsafe():
            assert v.base is obj

    def test_drop(self):
        """Test accessing after drop."""
        obj = self.get_obj()
        v = self.view_type(obj, ref=True)
        assert v.base is obj
        v.drop()
        with pytest.raises(errors.DroppedReferenceError):
            _ = v.base

    def test_is_gc(self):
        obj = self.get_obj()
        v = self.view_type(obj, ref=True)
        if gc.is_tracked(obj):
            assert v.is_gc()
            assert v.gc_is_tracked()
            assert v.gc_may_be_tracked()

        if not v.is_gc():
            assert not v.gc_is_tracked()
            assert not v.gc_may_be_tracked()

    def test_instance_dict(self):
        obj = self.get_obj()
        v = self.view_type(obj, ref=True)
        d = v._pyobject.instance_dict()
        if d is not None:
            assert d.contents.into_object() == obj.__dict__
            assert v.instance_dict == obj.__dict__
        else:
            # Accessing property should raise TypeError
            with pytest.raises(TypeError):
                _ = v.instance_dict


def test_base_weakref():
    """Access base after weakref is deleted."""

    class A:
        pass

    obj = A()
    v = AnyView(obj, ref=False)
    del obj
    with pytest.raises(errors.MovedError):
        _ = v.base
