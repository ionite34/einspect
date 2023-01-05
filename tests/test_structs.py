import pytest

from einspect import structs as st


class TestPyObject:
    def test_new(self):
        py_object = st.PyObject()
        assert py_object.ob_refcnt == 0

    def test_new_from_object(self):
        ls = []
        py_object = st.PyObject.from_object(ls)
        assert py_object.ob_refcnt == 1
        assert py_object.ob_type.contents.into_object().value == list

    @pytest.mark.parametrize(["obj", "ob_type"], [
        ("hello", str),
        (1, int),
        (1.0, float),
        (True, bool),
        (None, type(None)),
    ])
    def test_obj(self, obj, ob_type):
        py_object = st.PyObject.from_object(obj)
        assert py_object.ob_refcnt >= 1
        assert py_object.ob_type.contents.into_object().value == ob_type


class TestPyListObject:
    def test_size(self):
        ls = [1, 2, 3]
        pylist = st.PyListObject.from_object(ls)
        assert pylist.ob_size == 3
        pylist.ob_size = 2
        assert ls == [1, 2]


@pytest.mark.parametrize(["obj", "struct", "size"], [
    (False, st.PyBoolObject, (3 * 8)),
    (True, st.PyBoolObject, (3 * 8) + 4),
    (0, st.PyLongObject, (3 * 8)),
    (50, st.PyLongObject, (3 * 8) + 4),
    ((1, 2), st.PyTupleObject, (3 * 8) + (2 * 8)),
])
def test_mem_size_sizeof(obj, struct, size):
    """Test for structs matching __sizeof__."""
    py_object = struct.from_object(obj)
    assert py_object.mem_size == obj.__sizeof__()
    assert py_object.mem_size == size


@pytest.mark.parametrize(["obj", "struct", "delta"], [
    ([1, 2], st.PyListObject, lambda s: s.allocated * 8),
    ([1, 2, 3], st.PyListObject, lambda s: s.allocated * 8),
    # ({"A": 1, "B": 2}, st.PyDictObject, 0),
])
def test_mem_size_basic(obj, struct, delta):
    """
    Test for structs not matching __sizeof__.

    delta is bytes mem_size is smaller than __sizeof__.
    """
    py_object = struct.from_object(obj)
    delta = delta(py_object) if callable(delta) else delta
    assert py_object.mem_size == obj.__sizeof__() - delta
    assert py_object.mem_size == type(obj).__basicsize__
