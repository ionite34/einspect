from __future__ import annotations

import ctypes
from collections.abc import Sequence
from ctypes import addressof, c_uint32, sizeof

from typing_extensions import Annotated

from einspect.api import seq_to_array
from einspect.structs.deco import struct
from einspect.structs.py_object import Fields, PyVarObject
from einspect.types import Array


@struct
class PyLongObject(PyVarObject[int, None, None]):
    """
    Defines a PyLongObject Structure.

    https://github.com/python/cpython/blob/3.11/Include/cpython/longintrepr.h#L79-L82
    """

    _ob_digit_0: ctypes.c_uint32 * 0

    def _format_fields_(self) -> Fields:
        return {**super()._format_fields_(), "ob_digit": "Array[c_uint32]"}

    @property
    def mem_size(self) -> int:
        """Return the size of the PyObject in memory."""
        # Need to add size(uint32) * ob_size to our base size
        base = super().mem_size
        # use size 1 if ob_size is 0 due to allocation
        size = max(1, abs(self.ob_size))
        return base + ctypes.sizeof(c_uint32) * size

    @property
    def ob_digit(self) -> Array[Annotated[int, c_uint32]]:
        # Note PyLongObject uses the sign bit of ob_size to indicate its own sign
        # ob_size < 0 means the number is negative
        # ob_size > 0 means the number is positive
        # ob_size == 0 means the number is zero
        # The true size of the ob_digit array is abs(ob_size)
        items_addr = ctypes.addressof(self._ob_digit_0)
        size = max(abs(int(self.ob_size)), 1)
        return (c_uint32 * size).from_address(items_addr)  # type: ignore

    @ob_digit.setter
    def ob_digit(self, value: Array[int | c_uint32] | Sequence[int]) -> None:
        arr = seq_to_array(value, c_uint32)
        ctypes.memmove(
            addressof(self._ob_digit_0),
            addressof(arr),
            sizeof(arr),
        )

    @property
    def value(self) -> int:
        if self.ob_size == 0:
            return 0
        digit: int  # noqa: F842
        val = sum(digit * 1 << (30 * i) for i, digit in enumerate(self.ob_digit))
        size: int = self.ob_size  # type: ignore
        return val * (-1 if size < 0 else 1)
