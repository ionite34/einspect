from __future__ import annotations

import ctypes
from ctypes import Array
from typing import Sequence, TypeVar, overload

from einspect.api import Py_ssize_t
from einspect.compat import abc
from einspect.errors import UnsafeIndexError
from einspect.structs import PyObject, PyTupleObject
from einspect.utils import new_ref
from einspect.views.unsafe import unsafe
from einspect.views.view_base import VarView

__all__ = ("TupleView",)

_VT = TypeVar("_VT")


class TupleView(VarView[tuple, None, _VT], abc.Sequence):
    _pyobject: PyTupleObject[_VT]

    @overload
    def __getitem__(self, index: int) -> _VT:
        ...

    @overload
    def __getitem__(self, index: slice) -> tuple[_VT]:
        ...

    def __getitem__(self, index: int | slice) -> _VT | tuple[_VT]:
        if isinstance(index, int):
            # First use api GetItem
            try:
                ptr = self._pyobject.GetItem(index)
                py_struct = ptr.contents
                py_obj = py_struct.into_object()
                return py_obj.value
            except IndexError as err:
                raise IndexError(f"Index {index} out of range") from err
        elif isinstance(index, slice):
            start = index.start if index.start is not None else 0
            stop = index.stop if index.stop is not None else self.size
            ptr = self._pyobject.GetSlice(start, stop)
            return ptr.contents.into_object().value
        else:
            raise TypeError(f"Invalid index type: {type(index)}")

    def __setitem__(self, index: int, value: _VT) -> None:
        if isinstance(index, slice):
            raise ValueError("Cannot set slice of tuple")
        try:
            ref = PyObject.from_object(value).as_ref()
            self.item[index] = ref
        except IndexError as err:
            if not self._unsafe:
                raise UnsafeIndexError(
                    "Setting indices beyond current size requires entering an unsafe context."
                ) from err
            else:
                if index < 0:
                    raise IndexError(f"Index {index} out of range") from err

                # If unsafe, use direct set by creating a new array
                # noinspection PyProtectedMember
                start_addr = ctypes.addressof(self._pyobject._ob_item_0)
                # Size should be higher of the current size and the index
                size = max(self.size, index + 1)
                arr = (Py_ssize_t * size).from_address(start_addr)
                arr[index] = new_ref(value)

    def __len__(self) -> int:
        return self.size

    @property
    def item(self) -> Array[Py_ssize_t]:
        return self._pyobject.ob_item

    @item.setter
    @unsafe
    def item(self, value: Array[Py_ssize_t] | Sequence[int]) -> None:
        if isinstance(value, Array):
            # For Array, we can just copy the memory
            ctypes.memmove(self._pyobject.ob_item, value, ctypes.sizeof(value))
        else:
            # Get the memory address for the start of the array
            # noinspection PyProtectedMember
            start_addr = ctypes.addressof(self._pyobject._ob_item_0)
            # Get the size of the new array
            size = len(value)
            # Create a new array at the same address
            arr = (Py_ssize_t * size).from_address(start_addr)
            # Copy the values
            arr[:] = value
