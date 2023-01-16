from __future__ import annotations

import pytest

from einspect.structs import PyListObject
from einspect.views.factory import view
from einspect.views.view_list import ListView
from tests.views.test_view_base import TestView


class TestListView(TestView):
    view_type = ListView
    obj_type = list

    def get_obj(self):
        return [400, 500, 600]

    def test_sized(self):
        obj = self.get_obj()
        orig_len = len(obj)
        v = self.view_type(obj)
        assert len(v) == orig_len
        obj.pop()
        assert len(v) == orig_len - 1
        obj.clear()
        assert len(v) == 0

    def test_getitem(self):
        obj = self.get_obj()
        v = self.view_type(obj)
        assert v[0] == obj[0]
        assert v[1] == obj[1]
        assert v[2] == obj[2]
        assert v[:2] == obj[:2]
        assert v[::-1] == obj[::-1]
        assert v[:] == obj[:]

    def test_getitem_error(self):
        obj = self.get_obj()
        v = self.view_type(obj)
        with pytest.raises(IndexError):
            _ = v[len(obj)]
        with pytest.raises(TypeError):
            _ = v["abc"]  # type: ignore

    def test_setitem(self):
        obj = [1, 2, 3]
        v = self.view_type(obj)
        v[0] = 10
        v[1] = 20
        assert obj == [10, 20, 3]
        v[1:] = ["hi", "abc"]
        assert obj == [10, "hi", "abc"]
        v[:] = ("A", "B")
        assert obj == ["A", "B"]
