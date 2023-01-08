from textwrap import dedent
from einspect import view


def inline(s: str):
    return dedent(s).strip()


def test_info_int():
    x = 2 ** 32
    info = view(x).info()
    assert info == inline(f"""
    PyLongObject (at {hex(id(x))}):
       ob_refcnt: Py_ssize_t = 3
       ob_type: *PyTypeObject = &[int]
       ob_size: Py_ssize_t = 2
       ob_digit: Array[c_uint32] = [0, 4]
    """)
