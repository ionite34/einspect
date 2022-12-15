from __future__ import annotations

from ctypes import Array
from typing import Iterable, TypeVar

from einspect.api import Py_ssize_t
from einspect.structs import PyLongObject
from einspect.views.view_base import VarView

_T = TypeVar("_T")


class IntView(VarView[_T]):
    _pyobject: PyLongObject

    @property
    def digits(self) -> Array[Py_ssize_t]:
        return self._pyobject.ob_digit

    @digits.setter
    def digits(self, value: Iterable) -> None:
        self._pyobject.ob_digit[:] = value

    @property
    def value(self) -> int:
        return self._pyobject.value

    @value.setter
    def value(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError(f"Expected int, got {type(value).__name__!r}")
        # Get a struct of the new value
        cls = type(self._pyobject)
        new_val = cls.from_object(value)

        # The new value's ob_size must be equal or less than the current
        new_size = abs(new_val.ob_size)
        cur_size = abs(self._pyobject.ob_size)
        if new_size > cur_size:
            raise ValueError(f"New value {value!r} too large")

        # Copy the new value's digits into the current value
        self.digits[:new_size] = new_val.ob_digit

        # Set the new value's ob_size
        self._pyobject.ob_size = new_size
