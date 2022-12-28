import pytest

from einspect.structs import PyListObject
from einspect.views.factory import view
from einspect.views.view_list import ListView


@pytest.fixture(scope="function")
def obj() -> list[int]:
    return [1, 2, 3]


class TestListView:
    @pytest.mark.parametrize(["factory"], [
        (view,),
        (ListView,),
    ])
    def test_factory(self, obj, factory):
        """Test different ways of creating a ListView."""
        v = factory(obj)
        assert isinstance(v, ListView)
        assert isinstance(v._pyobject, PyListObject)
        assert v.size == len(obj)
        assert v.type == list
        assert ~v is obj

    def test_sized(self):
        ls = [1, 2]
        v = view(ls)
        assert len(v) == 2
        ls.pop()
        assert len(v) == 1
        ls.clear()
        assert len(v) == 0

    def test_getitem(self, obj):
        v = view(obj)
        assert v[0] == obj[0]
        assert v[1] == obj[1]
        assert v[2] == obj[2]
        assert v[:2] == obj[:2]
        assert v[:] == obj[:]

    def test_setitem(self):
        ls = [1, 2, 3]
        v = view(ls)
        v[0] = 10
        v[1] = 20
        assert ls == [10, 20, 3]
        v[1:] = ["hi", "abc"]
        assert ls == [10, "hi", "abc"]
        v[:] = ("A", "B")
        assert ls == ["A", "B"]
