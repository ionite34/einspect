import pytest

from einspect import view
from einspect.views.view_int import IntView
from einspect.structs import PyLongObject


class TestIntView:
    @pytest.mark.parametrize(["obj", "size"], [
        (1, 1),
        (2 ** 8, 1),
        (0, 0),  # CPython detail where 0 has ob_size of 0
        (-1, -1),
        (-9000, -1),
    ])
    def test_factory(self, obj, size):
        v = view(obj)
        assert isinstance(v, IntView)
        assert isinstance(v._pyobject, PyLongObject)
        assert v.type == int
        assert v.size == size
        assert v.value == obj
