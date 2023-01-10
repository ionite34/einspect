import ctypes

import pytest

from einspect.views import BoolView
from einspect.views.view_int import IntView
from tests.views.test_view_base import TestView


class TestIntView(TestView):
    view_type = IntView
    obj_type = int

    def get_obj(self):
        return 2**128 + 5

    def test_digits(self):
        obj = self.get_obj()
        v = self.view_type(obj)
        assert isinstance(v.digits, ctypes.Array)
        assert isinstance(v.digits[0], int)

    def test_value(self):
        obj = self.get_obj()
        v = self.view_type(obj)
        assert v.value == obj


class TestBoolView(TestIntView):
    view_type = BoolView
    obj_type = bool

    def get_obj(self):
        return False

    def test_memsize(self):
        v = self.view_type(True)
        expect_size = True.__sizeof__()
        assert v.mem_size == expect_size

    def test_singleton_true(self):
        v = self.view_type(True)
        assert v.size == 1
        assert v.digits[0] == 1

    def test_singleton_false(self):
        v = self.view_type(False)
        assert v.size == 0
        assert v.digits[0] == 0
