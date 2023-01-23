from __future__ import annotations

from types import MappingProxyType

import pytest

from einspect.views.view_mapping_proxy import MappingProxyView
from tests import dedent_text
from tests.views.test_view_base import TestView


@pytest.fixture(scope="function")
def obj() -> MappingProxyType[str, int]:
    d = {"a": 1, "b": 2}
    return MappingProxyType(d)


class TestMappingProxyView(TestView):
    view_type = MappingProxyView
    obj_type = MappingProxyType

    @staticmethod
    def get_dict() -> dict[str, int]:
        return {"a": 1, "b": 2}

    def get_obj(self) -> MappingProxyType[str, int]:
        return MappingProxyType(self.get_dict())

    def test_mapping(self):
        obj = self.get_obj()
        v = self.view_type(obj)
        assert isinstance(v.mapping, dict)
        assert v.mapping == self.get_dict()

    def test_getitem(self):
        obj = self.get_obj()
        v = self.view_type(obj)
        assert v["a"] == 1
        assert v["b"] == 2
        with pytest.raises(KeyError):
            assert not v["c"]

    def test_setitem(self):
        d = {"a": 1, "b": 2}
        obj = MappingProxyType(d)
        v = self.view_type(obj)

        assert v["a"] == 1
        assert d["a"] == 1
        v["a"] = "new"
        assert v["a"] == "new"
        assert d["a"] == "new"

    def test_delitem(self):
        d = {"a": 1, "b": 2}
        obj = MappingProxyType(d)
        v = self.view_type(obj)
        assert "a" in v
        del v["a"]
        assert "a" not in v
        assert "a" not in d

    def test_info(self):
        d = {"a": 1, "b": 2}
        obj = MappingProxyType(d)
        v = self.view_type(obj)
        assert v.info() == dedent_text(
            f"""
            MappingProxyObject (at {hex(id(obj))}):
               ob_refcnt: Py_ssize_t = 2
               ob_type: *PyTypeObject = &[mappingproxy]
               mapping: *PyDictObject = &[{{'a': 1, 'b': 2}}]
            """
        )
