from __future__ import annotations

import ctypes

import pytest

from einspect.structs import PyTupleObject
from einspect.views.factory import view
from einspect.views.view_tuple import TupleView


@pytest.fixture(scope="function")
def obj() -> tuple[int, int, int]:
    tup = (25, 50, 100)
    return tup


class TestTupleView:
    @pytest.mark.parametrize(["factory"], [
        (view,),
        (TupleView,),
    ])
    def test_factory(self, obj, factory):
        """Test different ways of creating a ListView."""
        v = factory(obj)
        assert isinstance(v, TupleView)
        assert isinstance(v._pyobject, PyTupleObject)
        assert v.size == len(obj)
        assert v.type == tuple
        assert isinstance(v.item, ctypes.Array)
        assert v.item[0] == id(obj[0])

    def test_get_item(self, obj):
        v = view(obj)
        assert v[0] == obj[0]
        assert v[1] == obj[1]
        assert v[2] == obj[2]
        assert v[:2] == obj[:2]
        assert v[:] == obj[:]

    def test_error_set_slice(self):
        v = view((1, 2, 3))
        with pytest.raises(ValueError):
            v[1:2] = (1, 2)


@pytest.mark.run_in_subprocess
def test_tuple_setitem():
    tup = ("test", 1, 2.0)
    v = view(tup)
    v[0] = "hm"
    v[1] = 4
    v[2] = 5
    assert tup == ("hm", 4, 5)
