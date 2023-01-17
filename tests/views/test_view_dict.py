import pytest

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
        assert len(v) == len(obj)

    def test_iter(self):
        d = {"a": 1, "b": 2}
        v = self.view_type(d)
        assert list(v) == list(d)
        for a, b in zip(v, d):
            assert a == b

    def test_getitem(self):
        obj = {"a": 1, "b": 2}
        v = self.view_type(obj)
        assert v["a"] == 1
        assert v["b"] == 2
        with pytest.raises(KeyError):
            assert not v["c"]

    def test_setitem(self):
        obj = {"a": 1, "b": 2}
        v = self.view_type(obj)
        v["a"] = 100
        assert v["a"] == 100
        assert obj["a"] == 100
        assert obj == {"a": 100, "b": 2}
        v["c"] = 3
        assert obj == {"a": 100, "b": 2, "c": 3}

    def test_delitem(self):
        obj = {"a": 1, "b": 2}
        v = self.view_type(obj)
        del v["a"]
        assert obj == {"b": 2}

        with pytest.raises(KeyError):
            del v["a"]

        with pytest.raises(KeyError):
            del v["not_exists"]
