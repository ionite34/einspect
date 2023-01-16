from __future__ import annotations

from ast import literal_eval

import pytest

from einspect.views.factory import view
from einspect.views.view_tuple import TupleView
from tests.views.test_view_base import TestView


class TestTupleView(TestView):
    view_type = TupleView
    obj_type = tuple

    def get_obj(self):
        return literal_eval("(1.2, 2.7, 3.0)")

    def test_item(self):
        obj = self.get_obj()
        v = self.view_type(obj)
        assert v.item[0].contents.into_object() is obj[0]

    def test_get_item(self):
        obj = self.get_obj()
        v = self.view_type(obj)
        assert v[0] == obj[0]
        assert v[1] == obj[1]
        assert v[2] == obj[2]
        assert v[:2] == obj[:2]
        assert v[:] == obj[:]

    def test_get_item_error(self):
        obj = self.get_obj()
        v = self.view_type(obj)
        with pytest.raises(IndexError):
            _ = v[len(obj)]

    def test_error_set_slice(self):
        obj = self.get_obj()
        v = self.view_type(obj)
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
