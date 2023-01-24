import pytest

from einspect.protocols.delayed_bind import bind_api, delayed_bind


def test_no_types():
    # No type hints should fail
    class Foo:
        @bind_api(lambda: None)
        def bar(self):
            pass

    with pytest.raises(TypeError):
        assert not Foo.bar


def test_repr():
    class Foo:
        @bind_api(lambda: None)
        def bar(self) -> int:
            pass

        assert repr(bar) == "<delayed_bind property None>"


def test_not_support_slots():
    class Foo:
        __slots__ = ()

        @bind_api(lambda: None)
        def bar(self) -> int:
            pass

    with pytest.raises(TypeError):
        assert not Foo().bar()
