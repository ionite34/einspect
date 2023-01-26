from __future__ import annotations

import sys
from types import FunctionType

import pytest

from einspect.views import FunctionView
from tests.views.test_view_base import TestView


class TestFunctionView(TestView):
    view_type = FunctionView
    obj_type = FunctionType

    def get_obj(self) -> FunctionType:
        def foo():
            return 1

        return foo  # type: ignore

    def test_attrs(self):
        def foo():
            return 1

        v = self.view_type(foo)

        assert v.globals == foo.__globals__
        assert v.name == foo.__name__
        assert v.qualname == foo.__qualname__
        assert v.code == foo.__code__
        assert v.defaults == foo.__defaults__
        assert v.kwdefaults == foo.__kwdefaults__
        assert v.closure == foo.__closure__
        assert v.doc == foo.__doc__
        assert v.module == foo.__module__

        # Materialize dicts before testing
        getattr(foo, "__dict__")
        getattr(foo, "__annotations__")
        assert v.dict == foo.__dict__
        assert v.annotations == foo.__annotations__

    @pytest.mark.skipif(sys.version_info < (3, 10), reason="Python 3.10+ only")
    def test_builtins(self):
        obj = self.get_obj()
        v = self.view_type(obj)
        assert v.builtins == obj.__globals__["__builtins__"]

    def test_globals(self):
        # noinspection PyUnresolvedReferences
        def foo():
            return stuff

        with pytest.raises(NameError):
            foo()

        # inject globals
        v = self.view_type(foo)
        with v.unsafe():
            v.globals = {"stuff": 123}

        assert foo() == 123
