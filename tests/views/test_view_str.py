from ast import literal_eval
from contextlib import ExitStack
from uuid import uuid4

import pytest

from einspect import view
from einspect.errors import UnsafeError
from einspect.structs import Kind, PyCompactUnicodeObject, State
from einspect.views.view_str import StrView
from tests.views.test_view_base import TestView


class TestStrView(TestView):
    view_type = StrView
    obj_type = str

    def get_obj(self) -> str:
        return literal_eval("'2fe7b604-9664-41e6-9af0-9b472864bfc8'")

    def test_unicode(self) -> None:
        text = literal_eval("'🤔'")
        v = view(text)
        assert v.buffer[0] == ord("🤔")
        assert isinstance(v._pyobject, PyCompactUnicodeObject)

    def test_properties(self) -> None:
        text = self.get_obj()
        v = view(text)
        assert v.length == len(text)
        expected_hash = hash(text)
        assert v.hash == expected_hash
        assert v.kind == Kind.PyUnicode_1BYTE

    def test_unsafe_resize(self) -> None:
        text = "abc"
        v = view(text)
        with pytest.raises(UnsafeError):
            v.append("x" * 64)

    def test_intern(self) -> None:
        text = self.get_obj()
        str_view = view(text)
        # Module level literal should be not interned
        assert str_view.interned == State.NOT_INTERNED
        # Create a function-level interned string
        s = "hi"
        assert view(s).interned == State.INTERNED_MORTAL

    def test_setters(self) -> None:
        text = self.get_obj()
        v = self.view_type(text)

        with ExitStack() as stack, v.unsafe():
            # Check -1 hash will reset the hash cache
            v.hash = -1
            assert v.hash == -1
            hash(text)
            assert v.hash == hash(text)
            assert v.hash != -1

            orig_len = len(text)
            assert v.length == orig_len
            stack.callback(lambda: setattr(v, "length", orig_len))
            v.length = orig_len // 2
            assert len(text) == orig_len // 2

            assert v.interned == State.NOT_INTERNED
            stack.callback(lambda: setattr(v, "interned", State.NOT_INTERNED))
            v.interned = State.INTERNED_MORTAL
            assert v.interned == State.INTERNED_MORTAL

            assert v.kind == Kind.PyUnicode_1BYTE
            stack.callback(lambda: setattr(v, "kind", Kind.PyUnicode_1BYTE))
            v.kind = Kind.PyUnicode_2BYTE
            assert v.kind == Kind.PyUnicode_2BYTE

    def test_buffer(self) -> None:
        text = self.get_obj()
        str_view = view(text)
        assert str_view.buffer[:] == text.encode("ascii")


def test_str_setitem() -> None:
    s = uuid4().hex
    orig_len = len(s)
    v = StrView(s)
    assert v.interned == State.NOT_INTERNED
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


def test_str_mutable_sequence() -> None:
    s = uuid4().hex
    orig_len = len(s)
    last = s[-1]
    v = StrView(s)
    assert v.pop() == last
    v.append("@")
    assert s[-1] == "@"
    assert len(s) == orig_len


def test_str_remove() -> None:
    s = literal_eval("'4ff4-e1219224-5462'")
    assert s is not "4ff4-e1219224-5462"
    v = StrView(s)
    assert v.interned == State.NOT_INTERNED
    v.remove("1219224")
    assert s == "4ff4-e-5462"
    # Removes only first instance
    v.remove("-")
    assert s == "4ff4e-5462"
