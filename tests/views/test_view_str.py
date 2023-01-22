from uuid import uuid4

import pytest

from einspect import view
from einspect.structs.py_unicode import Kind, State
from einspect.views.view_str import StrView
from tests.views.test_view_base import TestView


class TestStrView(TestView):
    view_type = StrView
    obj_type = str

    def get_obj(self) -> str:
        return "2fe7b604-9664-41e6-9af0-9b472864bfc8"

    def test_properties(self):
        text = self.get_obj()
        str_view = view(text)
        assert str_view.length == len(text)
        expected_hash = hash(text)
        assert str_view.hash == expected_hash
        assert str_view.kind == Kind.PyUnicode_1BYTE

    def test_intern(self):
        text = self.get_obj()
        str_view = view(text)
        # Module level literal should be not interned
        assert str_view.interned == State.NOT_INTERNED
        # Create a function-level interned string
        s = "hi"
        assert view(s).interned == State.INTERNED_MORTAL

    def test_buffer(self):
        text = self.get_obj()
        str_view = view(text)
        assert str_view.buffer[:] == text.encode("ascii")


def test_str_setitem():
    s = uuid4().hex
    orig_len = len(s)
    v = StrView(s)
    v[0] = "1"
    v[-1] = "Z"
    assert s[0] == "1"
    assert s[-1] == "Z"

    # Setting > 1 character should raise an error
    with pytest.raises(ValueError):
        v[0] = "123"
    # But 0 characters should be fine (same as del)
    v[0] = ""
    assert len(s) == orig_len - 1


def test_str_mutable_sequence():
    s = uuid4().hex
    orig_len = len(s)
    last = s[-1]
    v = StrView(s)
    assert v.pop() == last
    v.append("@")
    assert s[-1] == "@"
    assert len(s) == orig_len
