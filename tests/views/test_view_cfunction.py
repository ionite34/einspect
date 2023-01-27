from __future__ import annotations

from types import BuiltinFunctionType

from einspect.views import CFunctionView
from tests.views.test_view_base import TestView


class TestCFunctionView(TestView):
    view_type = CFunctionView
    obj_type = BuiltinFunctionType

    def get_obj(self) -> BuiltinFunctionType:
        return abs  # type: ignore

    def test_attrs(self):
        fn = self.get_obj()
        v = self.view_type(fn)

        assert v.ml.ml_name == fn.__name__.encode()
        assert v.ml.ml_doc.decode().endswith(fn.__doc__)
        assert v.self == fn.__self__
        assert v.module == fn.__module__
        assert v.weakreflist == v._pyobject.m_weakreflist.contents.into_object()
