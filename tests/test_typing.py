from __future__ import annotations

from typing import Union

from einspect._typing import is_union


def test_is_union():
    x = Union[int, str]
    assert is_union(x)
    assert not is_union(int)
