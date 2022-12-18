import ctypes

import pytest

from einspect.views.factory import view
from einspect.views.view_tuple import TupleView
from einspect.structs import PyTupleObject


@pytest.fixture(scope="function")
def obj():
    tup = ("test", 1, 2.0)
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
