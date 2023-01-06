import pytest

from einspect.structs import PySetObject
from einspect.views.factory import view
from einspect.views.view_set import SetView


@pytest.fixture(scope="function")
def obj() -> set[int]:
    return {1, 2, 3}


class TestSetView:
    @pytest.mark.parametrize(["factory"], [
        (view,),
        (SetView,),
    ])
    def test_factory(self, obj, factory):
        v = factory(obj)
        assert isinstance(v, SetView)
        assert isinstance(v._pyobject, PySetObject)
        assert v.type == set
        assert v.used == len(obj)
        assert v.base.value is obj
        assert ~v is obj
