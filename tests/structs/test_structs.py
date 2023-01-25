import ctypes
from ast import literal_eval

import pytest

from einspect import structs as st
from einspect.structs.py_gc import PyGC_Head
from einspect.structs.py_unicode import Kind


class UserClass:
    pass


class TestPyObject:
    def test_new(self):
        py_object = st.PyObject()
        assert py_object.ob_refcnt == 0

    def test_repr(self):
        ls = [1, 2]
        py_obj = st.PyObject.from_object(ls)
        assert repr(py_obj) == f"<PyObject[list] at {id(ls):#04x}>"

    def test_eq(self):
        """Two PyObjects at same address should be equal."""
        ls = [1, 2]
        obj_a = st.PyObject.from_object(ls)
        obj_b = st.PyObject.from_object(ls)
        ls_a = st.PyListObject.from_object(ls)
        assert obj_a == obj_b == ls_a

    def test_new_from_object(self):
        ls = []
        py_object = st.PyObject.from_object(ls)
        assert py_object.ob_refcnt == 1
        assert py_object.ob_type.contents.into_object() == list

    @pytest.mark.parametrize(
        ["obj", "ob_type"],
        [
            ("hello", str),
            (1, int),
            (1.0, float),
            (True, bool),
            (None, type(None)),
        ],
    )
    def test_obj(self, obj, ob_type):
        py_object = st.PyObject.from_object(obj)
        assert py_object.ob_refcnt >= 1
        assert py_object.ob_type.contents.into_object() == ob_type

    def test_api_setattr(self):
        obj = UserClass()
        py_object = st.PyObject.from_object(obj)
        py_object.SetAttr("hello", 123)
        assert getattr(obj, "hello") == 123

    def test_api_getattr(self):
        obj = UserClass()
        py_object = st.PyObject.from_object(obj)
        obj.xy = "test"
        assert py_object.GetAttr("xy") == "test"

    @pytest.mark.parametrize(
        ["obj", "expected"],
        [
            # Untracked types
            (True, False),
            (False, False),
            (None, False),
            (1, False),
            (15.75, False),
            ("hello", False),
            # Cached literal tuples aren't tracked
            ((), False),
            ((1, 2), False),
            (([1], [2]), True),
            # Tracked types
            ([], True),
            ({}, True),
            (set(), True),
            (frozenset(), True),
        ],
    )
    def test_gc_may_be_tracked(self, obj, expected):
        py_obj = st.PyObject.from_object(obj)
        assert py_obj.gc_may_be_tracked() == expected

    def test_gc_struct(self):
        t = [1, 2]
        py_obj = st.PyObject.from_object(t)
        gc_head = py_obj.as_gc()
        assert gc_head._gc_next != 0
        assert isinstance(gc_head.Next().contents, PyGC_Head)
        assert isinstance(gc_head.Prev().contents, PyGC_Head)
        assert gc_head.Finalized() is False


class TestPyListObject:
    def test_size(self):
        ls = [1, 2, 3]
        pylist = st.PyListObject.from_object(ls)
        assert pylist.ob_size == 3
        pylist.ob_size = 2
        assert ls == [1, 2]

    def test_item(self):
        ls = [1, 2]
        pylist = st.PyListObject.from_object(ls)
        assert pylist.ob_item[0].contents.into_object() == 1
        assert pylist.ob_item[1].contents.into_object() == 2

        pylist.ob_item[0] = st.PyObject.from_object(5).as_ref()
        assert ls == [5, 2]


class TestPyDictObject:
    def test_new(self):
        d = {1: 10, 5: 20}
        py_dict = st.PyDictObject.from_object(d)
        assert py_dict.ma_used == 2

    @pytest.mark.parametrize(
        ["obj", "indice_name"],
        [
            ({"hello": 123}, "c_char"),
            ({i: i for i in range(0xFF)}, "c_char"),
            ({i: i for i in range(0xFF)}, "c_int16"),
        ],
    )
    def test_dk_indices(self, obj: dict, indice_name):
        py_obj = st.PyDictObject.from_object(obj)
        keys = py_obj.ma_keys.contents
        # Check dk_indices
        assert isinstance(keys.dk_indices, ctypes.Array)
        indice_name = keys._dk_indices_type()[1]
        assert indice_name == indice_name

        # Check substructure format fields
        fields = keys._format_fields_()
        assert fields["dk_indices"] == f"Array[{indice_name}]"

        # Check main object format fields
        assert py_obj._format_fields_()


class TestPyUnicodeObject:
    @pytest.mark.parametrize(
        ["obj", "kind", "buffer"],
        [
            ("hello", Kind.PyUnicode_1BYTE, b"hello"),
            ("\ud83c\udf00", Kind.PyUnicode_2BYTE, [55356, 57088]),
            ("\U0001f300", Kind.PyUnicode_4BYTE, [127744]),
        ],
    )
    def test_kind(self, obj, kind, buffer):
        py_str = st.PyUnicodeObject.from_object(obj)
        assert py_str.kind == kind
        assert py_str.buffer[:] == buffer


class TestPyTypeObject:
    def test_new(self):
        py_int = st.PyTypeObject.from_object(int)
        repr_fn = py_int.tp_repr
        assert repr_fn(1) == "1"
        assert repr_fn(50) == "50"
        assert repr_fn(True) == "1"


class TestPyLongObject:
    def test_digit(self, new_int):
        obj = st.PyLongObject.from_object(new_int)
        assert len(obj.ob_digit[:]) == obj.ob_size
        py_obj = obj.into_object()
        assert py_obj == obj.value
        # Setting should work with any Sequence
        obj.ob_digit = [5]
        assert py_obj == 5
        # But not Generators, Iterators, etc.
        with pytest.raises(TypeError):
            obj.ob_digit = (i for i in range(5))


class TestPyTupleObject:
    def test_item(self):
        tup = literal_eval("(1,)")
        obj = st.PyTupleObject.from_object(tup)
        obj.ob_item = [st.PyObject.from_object(17).as_ref()]
        assert obj.into_object() == (17,)
        # Use array as well
        arr_type = type(obj.ob_item)
        obj.ob_item = arr_type(st.PyObject.from_object(5).as_ref())
        assert obj.into_object() == (5,)


@pytest.mark.parametrize(
    ["obj", "struct", "size"],
    [
        (True, st.PyBoolObject, (3 * 8) + 4),
        (50, st.PyLongObject, (3 * 8) + 4),
        ((1, 2), st.PyTupleObject, (3 * 8) + (2 * 8)),
    ],
)
def test_mem_size_sizeof(obj, struct, size):
    """Test for structs matching __sizeof__."""
    py_object = struct.from_object(obj)
    assert py_object.mem_size == obj.__sizeof__()
    assert py_object.mem_size == size


@pytest.mark.parametrize(
    ["obj", "struct", "delta"],
    [
        ([1, 2], st.PyListObject, lambda s: s.allocated * 8),
        ([1, 2, 3], st.PyListObject, lambda s: s.allocated * 8),
        # ({"A": 1, "B": 2}, st.PyDictObject, 0),
    ],
)
def test_mem_size_basic(obj, struct, delta):
    """
    Test for structs not matching __sizeof__.

    delta is bytes mem_size is smaller than __sizeof__.
    """
    py_object = struct.from_object(obj)
    delta = delta(py_object) if callable(delta) else delta
    assert py_object.mem_size == obj.__sizeof__() - delta
    assert py_object.mem_size == type(obj).__basicsize__


@pytest.mark.parametrize(
    ["src", "py_obj"],
    [
        (123, 123),
        (st.PyObject.from_object(123), 123),
        (st.PyObject.from_object(123).as_ref(), 123),
    ],
)
def test_try_from(src, py_obj):
    res = st.PyObject.try_from(src)
    assert res.into_object() == py_obj


def test_try_from_err_ctype():
    with pytest.raises(TypeError):
        st.PyObject.try_from(ctypes.c_void_p(0))
