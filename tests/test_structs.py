import pytest

from einspect import structs
from conftest import from_ptr


class TestPyObject:
    def test_new(self):
        py_object = structs.PyObject()
        assert py_object.ob_refcnt == 0

    def test_new_from_object(self):
        ls = []
        py_object = structs.PyObject.from_object(ls)
        assert py_object.ob_refcnt == 1
        assert from_ptr(py_object.ob_type) == list

    @pytest.mark.parametrize(["obj", "ob_type"], [
        ("hello", str),
        (1, int),
        (1.0, float),
        (True, bool),
        (None, type(None)),
    ])
    def test_obj(self, obj, ob_type):
        py_object = structs.PyObject.from_object(obj)
        assert py_object.ob_refcnt >= 1
        assert from_ptr(py_object.ob_type) == ob_type


class TestPyListObject:
    def test_size(self):
        ls = [1, 2, 3]
        pylist = structs.PyListObject.from_object(ls)
        assert pylist.ob_size == 3
        pylist.ob_size = 2
        assert ls == [1, 2]
