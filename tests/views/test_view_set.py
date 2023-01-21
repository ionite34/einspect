from __future__ import annotations

import weakref
from ctypes import addressof

from einspect.structs import PyObject
from einspect.views.view_set import SetView
from tests.views.test_view_base import TestView


class TestSetView(TestView):
    view_type = SetView
    obj_type = set

    def get_obj(self) -> set[int]:
        return {1, 2, 3}

    def test_fields(self):
        obj = {1, 2, 3}
        v = self.view_type(obj)
        assert v.fill == 3
        assert v.used == 3
        # Mask is 7, so table is 8 entries
        assert v.mask == 7
        assert len(v.table) == 8
        # This should still use the smalltable
        assert v.table[1].key.contents.into_object() == 1
        assert v.smalltable[1].key.contents.into_object() == 1
        assert addressof(v.table) == addressof(v.smalltable)

    def test_mask(self):
        # Mask should be table size - 1
        # Smalltable starts at 8, so mask should be 7
        obj = {"A", "B"}
        v = self.view_type(obj)
        assert v.mask == 7
        # Set the mask
        with v.unsafe():
            v.mask = 7

    def test_fill(self):
        obj = {"A", "B"}
        v = self.view_type(obj)
        assert v.fill == 2
        with v.unsafe():
            v.fill = 2

    def test_finger(self):
        obj = {11, 22, 33}
        v = self.view_type(obj)
        assert v.finger == 0
        assert obj.pop() == 33
        assert v.finger == 2
        assert obj.pop() == 11

    def test_set_finger(self):
        obj = {11, 22, 33}
        v = self.view_type(obj)
        with v.unsafe():
            v.finger = 2
        assert obj.pop() == 11
        assert v.finger == 4
        assert obj.pop() == 22

    def test_table(self):
        obj = {1, 2}
        v = self.view_type(obj)

        arr = v.table
        # Set entry 3
        arr[3].key = PyObject.from_object(3).as_ref()
        arr[3].hash = hash(3)
        with v.unsafe():
            # Increase our size
            v.used += 1
            # Set the array
            v.table = arr
            # Small table should be set as well
            assert v.smalltable[3].key.contents.into_object() == 3
            # but we'll set it anyway
            v.smalltable = arr
        assert 3 in obj
        assert obj == {1, 2, 3}

    def test_sized(self):
        obj = self.get_obj()
        orig_len = len(obj)
        v = self.view_type(obj)
        assert len(v) == orig_len
        obj.pop()
        assert len(v) == orig_len - 1
        obj.clear()
        assert len(v) == 0

    def test_weakref(self):
        obj = {"abc", "def"}
        v = self.view_type(obj)

        ref = v.weakreflist.contents.into_object()
        assert isinstance(ref, weakref.ReferenceType)
        assert ref() is obj

        with v.unsafe():
            v.weakreflist = PyObject.from_object(ref).as_ref()
