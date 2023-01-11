import pytest

from einspect.structs.include.object_h import PyNumberMethods
from einspect.structs.slots_map import Slot, get_slot


@pytest.mark.parametrize(
    ["name", "expected"],
    [
        ("__not_a_slot__", None),
        ("__add__", Slot("tp_as_number.nb_add", PyNumberMethods)),
        ("__name__", Slot("tp_name", None)),
    ],
)
def test_get_slot(name, expected):
    assert get_slot(name) == expected
