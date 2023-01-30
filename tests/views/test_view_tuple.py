from __future__ import annotations

from ast import literal_eval

import pytest

from einspect.errors import UnsafeError
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

    def test_set_item(self):
        obj = self.get_obj()
        v = self.view_type(obj)
        with v.unsafe():
            v.item = ["A", "B", "C"]
        assert v[0] == "A"
        assert obj == ("A", "B", "C")

    def test_get_item_error(self):
        obj = self.get_obj()
        v = self.view_type(obj)
        with pytest.raises(IndexError):
            _ = v[len(obj)]


def test_tuple_setitem():
    tup = literal_eval('("test", 1, 2.0)')
    v = TupleView(tup)
    v[0] = "hm"
    v[1] = 4
    v[2] = 5
    assert tup == ("hm", 4, 5)
    v[:] = (123, 456)
    assert tup == (123, 456)


def test_tuple_mutable_sequence():
    tup = literal_eval("(1, 2, 0)")
    v = TupleView(tup)
    assert v.pop() == 0
    v.append(3)
    assert tup == (1, 2, 3)

    # Extending too much
    with pytest.raises(UnsafeError):
        v.extend([1, 2, 3, 4, 5])

    with pytest.raises(UnsafeError):
        v.append(4)

    v[:] = (100, 200, 300)
    assert tup == (100, 200, 300)
    assert v.pop() == 300
    assert len(tup) == 2
    assert len(v) == 2

    v.insert(1, 123)
    assert tup == (100, 123, 200)
    assert v.pop(0) == 100
    v.clear()
    assert tup == ()
