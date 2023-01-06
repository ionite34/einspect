import pytest

from einspect.structs import PyDictObject
from einspect.views.factory import view
from einspect.views.view_dict import DictView


@pytest.fixture(scope="function")
def obj():
    return {
        "test": 1,
        2: 2.0
    }


class TestDictView:
    @pytest.mark.parametrize(["factory"], [
        (view,),
        (DictView,),
    ])
    def test_factory(self, obj, factory):
        """Test different ways of creating a ListView."""
        v = factory(obj)
        assert isinstance(v, DictView)
        assert isinstance(v._pyobject, PyDictObject)
        assert v.type == dict
        assert v.used == len(obj)
        assert v.base.value is obj
        assert ~v is obj
