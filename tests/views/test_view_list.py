import pytest

from einspect.views.factory import view
from einspect.views.view_list import ListView
from einspect.structs import PyListObject


@pytest.fixture(scope="function")
def obj():
    return [1, 2, 3]


class TestListView:
    @pytest.mark.parametrize(["factory"], [
        view,
        ListView,
     ])
    def test_factory(self, obj, factory):
        """Test different ways of creating a ListView."""
        v = factory(obj)
        assert isinstance(v, ListView)
        assert isinstance(v._pyobject, PyListObject)
        assert v.size == len(obj)
        assert v.type == list
