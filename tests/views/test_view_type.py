from __future__ import annotations

import pytest

from einspect.errors import UnsafeError
from einspect.views.view_type import TypeView
from tests.views.test_view_base import TestView


class TestTypeView(TestView):
    view_type = TypeView
    obj_type = type

    def get_obj(self) -> type[int]:
        return int

    @staticmethod
    def get_user_cls() -> type:
        class Foo:
            pass

        return Foo

    def test_py_obj_attrs(self):
        v = self.view_type(set)
        assert v.tp_name == b"set"

        with v.unsafe():
            v.tp_name = b"abc"

    def test_immutable(self):
        # int type should be immutable
        v = self.view_type(int)
        assert v.immutable is True
        # user defined class should be mutable
        v_user = self.view_type(self.get_user_cls())
        assert v_user.immutable is False

    def test_as_mutable_bypass(self):
        # Already mutable types should not be affected
        v = self.view_type(self.get_user_cls())
        assert v.immutable is False
        with v.as_mutable():
            assert v.immutable is False

    def test_getitem(self):
        # Test getitem for getting type attributes
        v = self.view_type(int)
        assert v["to_bytes"] is int.to_bytes
        # Other attributes should error
        with pytest.raises(AttributeError):
            assert not v["__iter__"]

    def test_alloc_mode(self):
        v = self.view_type(float)
        assert v._alloc_mode is None
        with v.alloc_mode("mapping"):
            assert v._alloc_mode == "mapping"

        with pytest.raises(ValueError):
            # noinspection PyTypeChecker
            with v.alloc_mode("abc"):
                pass


@pytest.mark.run_in_subprocess
def test_as_mutable():
    # Initial, setattr should fail
    with pytest.raises(TypeError):
        int.abc = "test"
    # Unlocking with as_mutable
    v = TypeView(int)
    with v.as_mutable():
        int.abc = "test"
        int.__repr__ = lambda self: "int_repr"
    # setattr should fail again after context exits
    with pytest.raises(TypeError):
        int.abc = "test"
    # Attributes should be set now
    assert int.abc == "test"
    assert repr(10) == "int_repr"


def test_setitem():
    v = TypeView(dict)

    # Setting attributes should fail
    with pytest.raises(TypeError):
        dict._abc_123 = "test"

    with pytest.raises(AttributeError):
        _ = v["_abc_123"]

    # Add the attribute
    v["_abc_123"] = lambda self: "test"
    # Check that it works
    # noinspection PyUnresolvedReferences
    assert dict()._abc_123() == "test"
