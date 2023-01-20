from __future__ import annotations

from ctypes import Array, c_uint32
from typing import Iterable, TypeVar

from typing_extensions import Annotated

from einspect.structs import PyLongObject
from einspect.views.view_base import VarView

__all__ = ("IntView",)

_T = TypeVar("_T")


class IntView(VarView[int, None, None]):
    _pyobject: PyLongObject

    @property
    def digits(self) -> Array[Annotated[int, c_uint32]]:
        return self._pyobject.ob_digit

    @digits.setter
    def digits(self, value: Iterable) -> None:
        self._pyobject.ob_digit[:] = value

    @property
    def value(self) -> int:
        return self._pyobject.value

    @value.setter
    def value(self, obj: int) -> None:
        if not isinstance(obj, int):
            raise TypeError(f"Expected int, got {type(obj).__name__!r}")
        # Get a struct of the new value
        cls = type(self._pyobject)
        new_val = cls.from_object(obj)

        # The new value's ob_size must be equal or less than the current
        new_size = abs(new_val.ob_size)
        cur_size = max(abs(self._pyobject.ob_size), 1)
        if new_size > cur_size:
            raise ValueError(f"New value {obj!r} too large")

        # Copy the new value's digits into the current value
        self.digits[:new_size] = new_val.ob_digit

        # Set the new value's ob_size
        self._pyobject.ob_size = new_size
