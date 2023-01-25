import pytest

from einspect.structs import PyObject


def test_from_gc() -> None:
    ls = [1, 2, 3]
    obj = PyObject.from_object(ls)
    assert obj.is_gc()
    gc_head = obj.as_gc()
    assert PyObject.from_gc(gc_head).into_object() is ls


@pytest.mark.run_in_subprocess
def test_gc_head_api():
    obj = ["test", "123"]
    py_obj = PyObject.from_object(obj)
    gc_head = py_obj.as_gc()

    assert gc_head.Set_Prev(gc_head.Prev()) is None
    assert gc_head.Set_Next(gc_head.Next()) is None
