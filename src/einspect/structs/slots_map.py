# Mapping of dunder names to their corresponding slot paths.
# https://docs.python.org/3/c-api/typeobj.html
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Sequence, Union

from einspect.structs.include.object_h import (
    PyAsyncMethods,
    PyMappingMethods,
    PyNumberMethods,
    PySequenceMethods,
)


@dataclass
class Slot:
    name: str
    ptr_type: type | None = None

    @property
    def parts(self) -> list[str]:
        return self.name.split(".")

    def __getitem__(self, slot: str | Slot):
        slot_name = slot.name if isinstance(slot, Slot) else slot
        return Slot(f"{self.name}.{slot_name}", self.ptr_type)


SlotsLike = Union[str, Slot, Sequence[Union[str, Slot]]]

tp_as_async = Slot("tp_as_async", PyAsyncMethods)
tp_as_number = Slot("tp_as_number", PyNumberMethods)
tp_as_sequence = Slot("tp_as_sequence", PySequenceMethods)
tp_as_mapping = Slot("tp_as_mapping", PyMappingMethods)

SLOTS_MAIN: Final[dict[str, SlotsLike]] = {
    "__name__": "tp_name",
    "__repr__": "tp_repr",
    "__hash__": "tp_hash",
    "__call__": "tp_call",
    "__str__": "tp_str",
    "__getattribute__": "tp_getattro",
    "__getattr__": "tp_getattro",
    "__setattr__": "tp_setattro",
    "__delattr__": "tp_setattro",
    "__doc__": "tp_doc",
    "__lt__": "tp_richcompare",
    "__le__": "tp_richcompare",
    "__eq__": "tp_richcompare",
    "__ne__": "tp_richcompare",
    "__gt__": "tp_richcompare",
    "__ge__": "tp_richcompare",
    "__iter__": "tp_iter",
    "__next__": "tp_iternext",
    "__base__": "tp_base",
    "__dict__": "tp_dict",
    "__get__": "tp_descr_get",
    "__set__": "tp_descr_set",
    "__delete__": "tp_descr_set",
    "__init__": "tp_init",
    "__new__": "tp_new",
    "__bases__": "tp_bases",
    "__mro__": "tp_mro",
    "__subclasses__": "tp_subclasses",
    "__del__": "tp_finalize",
}

SLOTS_SUB_ASYNC: Final[dict[str, SlotsLike]] = {
    "__await__": tp_as_async["am_await"],
    "__aiter__": tp_as_async["am_aiter"],
    "__anext__": tp_as_async["am_anext"],
}

SLOTS_NUMBERS: Final[dict[str, SlotsLike]] = {
    "__add__": tp_as_number["nb_add"],
    "__radd__": tp_as_number["nb_add"],
    "__iadd__": tp_as_number["nb_inplace_add"],
    "__sub__": tp_as_number["nb_subtract"],
    "__rsub__": tp_as_number["nb_subtract"],
    "__isub__": tp_as_number["nb_inplace_subtract"],
    "__mul__": tp_as_number["nb_multiply"],
    "__rmul__": tp_as_number["nb_multiply"],
    "__imul__": tp_as_number["nb_inplace_multiply"],
    "__mod__": tp_as_number["nb_remainder"],
    "__rmod__": tp_as_number["nb_remainder"],
    "__imod__": tp_as_number["nb_inplace_remainder"],
    "__divmod__": tp_as_number["nb_divmod"],
    "__rdivmod__": tp_as_number["nb_divmod"],
    "__pow__": tp_as_number["nb_power"],
    "__rpow__": tp_as_number["nb_power"],
    "__ipow__": tp_as_number["nb_inplace_power"],
    "__neg__": tp_as_number["nb_negative"],
    "__pos__": tp_as_number["nb_positive"],
    "__abs__": tp_as_number["nb_absolute"],
    "__bool__": tp_as_number["nb_bool"],
    "__invert__": tp_as_number["nb_invert"],
    "__lshift__": tp_as_number["nb_lshift"],
    "__rlshift__": tp_as_number["nb_lshift"],
    "__ilshift__": tp_as_number["nb_inplace_lshift"],
    "__rshift__": tp_as_number["nb_rshift"],
    "__rrshift__": tp_as_number["nb_rshift"],
    "__irshift__": tp_as_number["nb_inplace_rshift"],
    "__and__": tp_as_number["nb_and"],
    "__rand__": tp_as_number["nb_and"],
    "__iand__": tp_as_number["nb_inplace_and"],
    "__xor__": tp_as_number["nb_xor"],
    "__rxor__": tp_as_number["nb_xor"],
    "__ixor__": tp_as_number["nb_inplace_xor"],
    "__or__": tp_as_number["nb_or"],
    "__ror__": tp_as_number["nb_or"],
    "__ior__": tp_as_number["nb_inplace_or"],
    "__int__": tp_as_number["nb_int"],
    "__float__": tp_as_number["nb_float"],
    "__floordiv__": tp_as_number["nb_floor_divide"],
    "__ifloordiv__": tp_as_number["nb_inplace_floor_divide"],
    "__truediv__": tp_as_number["nb_true_divide"],
    "__itruediv__": tp_as_number["nb_inplace_true_divide"],
    "__index__": tp_as_number["nb_index"],
    "__matmul__": tp_as_number["nb_matrix_multiply"],
    "__imatmul__": tp_as_number["nb_inplace_matrix_multiply"],
}

SLOTS_SEQUENCE: Final[dict[str, SlotsLike]] = {
    "__len__": tp_as_sequence["sq_length"],
    "__add__": tp_as_sequence["sq_concat"],
    "__mul__": tp_as_sequence["sq_repeat"],
    "__getitem__": tp_as_sequence["sq_item"],
    "__setitem__": tp_as_sequence["sq_ass_item"],
    "__delitem__": tp_as_sequence["sq_ass_item"],
    "__contains__": tp_as_sequence["sq_contains"],
    "__iadd__": tp_as_sequence["sq_inplace_concat"],
    "__imul__": tp_as_sequence["sq_inplace_repeat"],
}

SLOTS_MAPPING: Final[dict[str, SlotsLike]] = {
    "__len__": tp_as_mapping["mp_length"],
    "__getitem__": tp_as_mapping["mp_subscript"],
    "__setitem__": tp_as_mapping["mp_ass_subscript"],
    "__delitem__": tp_as_mapping["mp_ass_subscript"],
}

# Set of all dunder slot names
SLOTS_NAMES: set[str] = {
    *SLOTS_MAIN.keys(),
    *SLOTS_SUB_ASYNC.keys(),
    *SLOTS_NUMBERS.keys(),
    *SLOTS_SEQUENCE.keys(),
    *SLOTS_MAPPING.keys(),
}

SLOTS = [
    SLOTS_MAIN,
    SLOTS_SUB_ASYNC,
    SLOTS_NUMBERS,
    SLOTS_SEQUENCE,
    SLOTS_MAPPING,
]


def get_slot(name: str) -> Slot | None:
    # Iterate the list to find a match
    for slots in SLOTS:
        if name in slots:
            res = slots[name]
            # Make a Slot if we got a str
            if isinstance(res, str):
                return Slot(res)
            return res
    return None
