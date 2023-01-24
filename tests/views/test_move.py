"""Test moving of views."""
from ast import literal_eval

import pytest

from einspect import view
from einspect.structs import PyLongObject, PyTypeObject


def get_int() -> int:
    """Return a new allocated int."""
    obj_st = PyLongObject(
        ob_refcnt=1,
        ob_type=PyTypeObject.from_object(int).as_ref(),
        ob_size=1,
        ob_digit=[100],
    )
    return obj_st.with_ref().into_object()


def test_move_op():
    x = get_int()
    v = view(x)
    with v.unsafe():
        v <<= 5
    assert x == 5
    assert id(x) != id(5)


def test_move_from():
    x = get_int()
    v = view(x)
    with v.unsafe():
        v.move_from(view(5))
    assert x == 5
    assert id(x) != id(5)


@pytest.mark.run_in_subprocess
def test_move_tuple():
    tup = literal_eval("(1, 2)")
    v = view(tup)
    with v.unsafe():
        v <<= ("A", "B", "C")

    assert tup == ("A", "B", "C")
