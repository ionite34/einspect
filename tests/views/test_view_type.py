from __future__ import annotations

import pytest

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

    def test_immutable(self):
        # int type should be immutable
        v = self.view_type(int)
        assert v.immutable is True
        # user defined class should be mutable
        v_user = self.view_type(self.get_user_cls())
        assert v_user.immutable is False

    def test_getitem(self):
        # Test getitem for getting type attributes
        v = self.view_type(int)
        assert v["to_bytes"] is int.to_bytes
        # Other attributes should error
        with pytest.raises(AttributeError):
            assert not v["__iter__"]


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


@pytest.mark.run_in_subprocess
def test_setitem():
    # Setitem should add attributes / slots
    v = TypeView(float)
    # This should fail initially
    with pytest.raises(AttributeError):
        assert not v["__iter__"]
    # Add an __iter__ method to float
    v["__iter__"] = lambda self: iter(range(int(self)))
    # Check that it works
    n = 12.1
    expect = list(range(12))
    # noinspection PyTypeChecker
    assert list(n) == expect
    assert [*n] == expect
