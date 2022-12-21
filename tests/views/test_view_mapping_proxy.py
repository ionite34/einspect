import pytest

from types import MappingProxyType

from einspect.views.factory import view
from einspect.views.view_mapping_proxy import MappingProxyView
from einspect.structs import MappingProxyObject


@pytest.fixture(scope="function")
def obj() -> MappingProxyType[str, int]:
    d = {"a": 1, "b": 2}
    return MappingProxyType(d)


class TestTupleView:
    @pytest.mark.parametrize(["factory"], [
        (view,),
        (MappingProxyView,),
    ])
    def test_factory(self, obj, factory):
        """Test different ways of creating a ListView."""
        v = factory(obj)
        assert isinstance(v, MappingProxyView)
        assert isinstance(v._pyobject, MappingProxyObject)
        assert v.type == MappingProxyType
        assert v.mapping == {"a": 1, "b": 2}
        assert v.base.value is obj
        assert ~v is obj
