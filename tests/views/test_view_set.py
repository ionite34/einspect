from __future__ import annotations

import pytest

from einspect.views.view_set import SetView
from tests.views.test_view_base import TestView


@pytest.fixture(scope="function")
def obj() -> set[int]:
    return {1, 2, 3}


class TestSetView(TestView):
    view_type = SetView
    obj_type = set

    def get_obj(self) -> set[int]:
        return {1, 2, 3}

    def test_sized(self):
        obj = self.get_obj()
        orig_len = len(obj)
        v = self.view_type(obj)
        assert len(v) == orig_len
        obj.pop()
        assert len(v) == orig_len - 1
        obj.clear()
        assert len(v) == 0
