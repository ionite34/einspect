import ctypes

import pytest

from einspect.api import ALIGNMENT
from einspect.structs import PyBoolObject, PyLongObject, PyTypeObject
from einspect.views import BoolView
from einspect.views.view_int import IntView
from tests.views.test_view_base import TestView


class TestIntView(TestView):
    view_type = IntView
    obj_type = int

    def get_obj(self):
        return 2**128 + 5

    def test_memsize(self):
        obj = self.get_obj()
        v = self.view_type(obj)
        expected = obj.__sizeof__()
        assert v.mem_size == expected

        if v.mem_size % ALIGNMENT == 0:
            assert v.mem_allocated == expected
        else:
            assert v.mem_allocated == expected + (ALIGNMENT - expected % ALIGNMENT)

    def test_digits(self):
        obj = self.get_obj()
        v = self.view_type(obj)
        assert isinstance(v.digits, ctypes.Array)
        assert isinstance(v.digits[0], int)

    def test_value(self):
        obj = self.get_obj()
        v = self.view_type(obj)
        assert v.value == obj

    def test_set_value(self):
        obj_st = PyLongObject(
            ob_refcnt=1,
            ob_type=PyTypeObject.from_object(int).as_ref(),
            ob_size=1,
            ob_digit=[900],
        )
        obj = obj_st.with_ref().into_object()
        assert obj == 900
        # Change the value
        v = self.view_type(obj)
        v.value = 1000
        assert obj == 1000


class TestBoolView(TestIntView):
    view_type = BoolView
    obj_type = bool

    def get_obj(self):
        return False

    def test_set_value(self):
        obj_st = PyBoolObject(
            ob_refcnt=1,
            ob_type=PyTypeObject.from_object(bool).as_ref(),
            ob_size=1,
            ob_digit=[1],
        )
        obj = obj_st.with_ref().into_object()
        assert obj == 1
        # Change the value
        v = self.view_type(obj)
        v.value = 1000
        assert obj == 1000

    def test_memsize(self):
        v = self.view_type(True)
        expected = True.__sizeof__()
        assert v.mem_size == expected

    def test_singleton_true(self):
        v = self.view_type(True)
        assert v.size == 1
        assert v.digits[0] == 1

    def test_singleton_false(self):
        v = self.view_type(False)
        assert v.size == 0
        assert v.digits[0] == 0
