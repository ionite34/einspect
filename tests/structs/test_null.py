"""Test behavior of the `types.NULL` singleton."""
from __future__ import annotations

from einspect import NULL
from einspect.structs import MappingProxyObject, PyObject, PyTupleObject, PyTypeObject


def test_func_ptr():
    """Test that NULL can be used as a function pointer."""

    t = PyTypeObject(int)
    n = t.tp_as_number.contents
    assert n.nb_add != NULL
    # Null FuncPtr should equal NULL
    assert n.nb_matrix_multiply == NULL
    # We can set this to NULL, and it'll invoke type(FuncPtr)()
    n.nb_matrix_multiply = NULL
    assert n.nb_matrix_multiply == NULL


def test_py_object_arr():
    """Test usage as a NULL PyObject pointer."""

    s = PyTupleObject(
        ob_refcnt=1,
        ob_type=PyTypeObject(tuple).as_ref(),
        ob_size=2,
        ob_item=[NULL] * 2,
    )
    assert not s.ob_item[0]
    assert not s.ob_item[1]
    assert s.ob_item[0] == NULL
    assert s.ob_item[1] == NULL

    # Set an object value
    s.ob_item[0] = PyObject(10).as_ref()
    assert s.ob_item[0].contents.into_object() == 10

    # Set back to NULL
    s.ob_item[0] = NULL
    assert not s.ob_item[0]


def test_py_object():
    """Test usage as a NULL PyObject pointer."""

    class Foo:
        x = 100

    # Materialize dict
    assert Foo.__dict__

    s = PyTypeObject(Foo)
    assert s.tp_dict != NULL

    # Set to NULL
    s.tp_dict = NULL
    assert s.tp_dict == NULL
