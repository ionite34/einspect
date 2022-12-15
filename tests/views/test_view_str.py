from copy import copy

import pytest

from einspect import view, structs
from einspect.structs.py_unicode import State, Kind
from einspect.views.view_str import StrView

TEXT = "2fe7b604-9664-41e6-9af0-9b472864bfc8"


@pytest.fixture(scope="module")
def str_view():
    return view(copy(TEXT), ref=True)


class TestStrView:
    def test_type(self, str_view):
        assert isinstance(str_view, StrView)
        assert isinstance(str_view._pyobject, structs.PyObject)

    def test_properties(self):
        x = "hello"
        x_hash = hash(x)
        v = view(x)
        assert type(v.length) == int
        assert v.length == 5

        assert type(v.hash) == int
        assert v.hash == x_hash

        assert v.kind == Kind.PyUnicode_1BYTE

    def test_intern(self, str_view):
        # str_view fixture view has no literal refs
        # so, it should not be interned
        assert str_view.interned == State.NOT_INTERNED

        # Create a function-level mortal interned string
        s = "hi"
        assert view(s).interned == State.INTERNED_MORTAL

    def test_buffer(self):
        """Access buffer."""
        obj = "hello"
        v = view(obj)
        assert v.buffer[:] == b"hello"
