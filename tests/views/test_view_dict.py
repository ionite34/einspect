import pytest

from einspect.structs import PyDictObject
from einspect.views.factory import view
from einspect.views.view_dict import DictView
from tests.views.test_view_base import TestView


class TestDictView(TestView):
    view_type = DictView
    obj_type = dict

    def get_obj(self):
        return {"a": 1, "b": 2}

    def test_dict(self):
        obj = self.get_obj()
        v = self.view_type(obj)
        assert v.type is dict
        assert v.used == len(obj)
        # assert v.ma_keys.contents == 0
