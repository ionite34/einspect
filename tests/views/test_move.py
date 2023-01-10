"""Test moving of views."""
from ast import literal_eval

import pytest

from einspect import view


def test_move_op():
    x = literal_eval("1593020931")
    v = view(x)
    with v.unsafe():
        v <<= 5
    assert x == 5
    assert id(x) != id(5)


def test_move_from():
    x = literal_eval("2905504286")
    v = view(x)
    with v.unsafe():
        v.move_from(view(5))
    assert x == 5
    assert id(x) != id(5)
