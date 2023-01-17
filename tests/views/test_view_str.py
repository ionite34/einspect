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
