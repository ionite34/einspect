from einspect import view
from tests import dedent_text


def test_info_int() -> None:
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


def test_info_list() -> None:
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


def test_info_set() -> None:
    x = {1, 2, 3}
    info = view(x).info()
    # Skip last line
    info = "\n".join(info.splitlines()[:-1])
    assert (
        info
        == dedent_text(
            """
        PySetObject (at <id>):
           ob_refcnt: Py_ssize_t = 2
           ob_type: *PyTypeObject = &[set]
           fill: Py_ssize_t = 3
           used: Py_ssize_t = 3
           mask: Py_ssize_t = 7
           table: *SetEntry = &[{ key = &[NULL], hash = 0 }]
           hash: Py_hash_t = -1
           finger: Py_ssize_t = 0
           smalltable: Array[SetEntry] = [
              { key = &[NULL], hash = 0 },
              { key = &[1], hash = 1 },
              { key = &[2], hash = 2 },
              { key = &[3], hash = 3 },
              { key = &[NULL], hash = 0 },
              { key = &[NULL], hash = 0 },
              { key = &[NULL], hash = 0 },
              { key = &[NULL], hash = 0 }
           ]
        """
        ).replace("<id>", hex(id(x)))
    )
