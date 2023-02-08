"""Test behavior of the `types.NULL` singleton."""
from __future__ import annotations

from einspect import NULL
from einspect.structs import PyTupleObject, PyTypeObject


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


def test_py_object():
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
