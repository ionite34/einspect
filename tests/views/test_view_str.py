import pytest

from einspect import structs, view
from einspect.structs.py_unicode import Kind, State
from einspect.views.view_str import StrView

TEXT = "2fe7b604-9664-41e6-9af0-9b472864bfc8"


@pytest.fixture(scope="function")
def str_view() -> StrView:
    return view(TEXT, ref=True)


class TestStrView:
    def test_type(self, str_view):
        assert isinstance(str_view, StrView)
        assert isinstance(str_view._pyobject, structs.PyObject)

    def test_properties(self, str_view):
        assert str_view.length == len(TEXT)
        expected_hash = hash(TEXT)
        assert str_view.hash == expected_hash
        assert str_view.kind == Kind.PyUnicode_1BYTE

    def test_intern(self, str_view):
        # Module level literal should be not interned
        assert str_view.interned == State.NOT_INTERNED
        # Create a function-level interned string
        s = "hi"
        assert view(s).interned == State.INTERNED_MORTAL

    def test_buffer(self, str_view):
        assert str_view.buffer[:] == TEXT.encode("ascii")
