"""Test moving of views."""
from ast import literal_eval
from random import randint

import pytest

from einspect import view
from einspect.structs import PyLongObject, PyTupleObject, PyTypeObject


def test_move_op(new_int):
    v = view(new_int)
    with v.unsafe():
        v <<= 5
    assert new_int == 5
    assert id(new_int) != id(5)


def test_move_from(new_int):
    v = view(new_int)
    with v.unsafe():
        v.move_from(view(5))
    assert new_int == 5
    assert id(new_int) != id(5)
