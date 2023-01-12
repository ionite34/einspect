from __future__ import annotations

from types import MappingProxyType

import pytest

from einspect.structs import MappingProxyObject
from einspect.views.factory import view
from einspect.views.view_mapping_proxy import MappingProxyView


@pytest.fixture(scope="function")
def obj() -> MappingProxyType[str, int]:
    d = {"a": 1, "b": 2}
    return MappingProxyType(d)


class TestTupleView:
    @pytest.mark.parametrize(
        ["factory"],
        [
            (view,),
            (MappingProxyView,),
        ],
    )
    def test_factory(self, obj, factory):
        """Test different ways of creating a ListView."""
        v = factory(obj)
        assert isinstance(v, MappingProxyView)
        assert isinstance(v._pyobject, MappingProxyObject)
        assert v.type == MappingProxyType
        assert v.mapping == {"a": 1, "b": 2}
        assert v.base is obj
        assert ~v is obj
