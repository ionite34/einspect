from einspect import view, structs
from einspect.structs.py_unicode import State, Kind
from einspect.views.view_str import StrView

TEXT = "2fe7b604-9664-41e6-9af0-9b472864bfc8"


class TestStrView:
    def setup(self):
        self.view = view(TEXT, ref=True)

    def test_type(self):
        assert isinstance(self.view, StrView)
        assert isinstance(self.view._pyobject, structs.PyObject)

    def test_properties(self):
        assert self.view.length == len(TEXT)
        expected_hash = hash(TEXT)
        assert self.view.hash == expected_hash
        assert self.view.kind == Kind.PyUnicode_1BYTE

    def test_intern(self):
        # Module level literal should be not interned
        assert self.view.interned == State.NOT_INTERNED
        # Create a function-level interned string
        s = "hi"
        assert view(s).interned == State.INTERNED_MORTAL

    def test_buffer(self):
        assert self.view.buffer[:] == TEXT.encode("ascii")
