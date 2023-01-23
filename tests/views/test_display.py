from textwrap import dedent

from einspect import view
from tests import dedent_text


def test_info_int():
    x = 2**32
    info = view(x).info()
    assert info == dedent_text(
        f"""
        PyLongObject (at {hex(id(x))}):
           ob_refcnt: Py_ssize_t = 3
           ob_type: *PyTypeObject = &[int]
           ob_size: Py_ssize_t = 2
           ob_digit: Array[c_uint32] = [0, 4]
        """
    )


def test_info_list():
    x = [1, "A"]
    info = view(x).info()
    assert info == dedent_text(
        f"""
        PyListObject (at {hex(id(x))}):
           ob_refcnt: Py_ssize_t = 2
           ob_type: *PyTypeObject = &[list]
           ob_size: Py_ssize_t = 2
           ob_item: **PyObject = &[&[1], &['A']]
           allocated: c_long = 2
        """
    )
