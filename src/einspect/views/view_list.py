from __future__ import annotations

from collections.abc import Sequence
from ctypes import POINTER, addressof, memmove, sizeof
from typing import TypeVar, overload

from einspect.api import seq_to_array
from einspect.compat import abc
from einspect.structs import PyListObject, PyObject
from einspect.types import Array, ptr
from einspect.views.unsafe import unsafe
from einspect.views.view_base import REF_DEFAULT, VarView

__all__ = ("ListView",)

_VT = TypeVar("_VT")


class ListView(VarView[list, None, _VT], abc.Sequence[_VT]):
    _pyobject: PyListObject[_VT]

    def __init__(self, obj: list[_VT], ref: bool = REF_DEFAULT) -> None:
        super().__init__(obj, ref)

    @overload
    def __getitem__(self, index: int) -> _VT:
        ...

    @overload
    def __getitem__(self, index: slice) -> list[_VT]:
        ...

    def __getitem__(self, index: int | slice) -> _VT | list[_VT]:
        if isinstance(index, int):
            obj_ptr = self._pyobject.GetItem(index)
            return obj_ptr.contents.into_object()
        elif isinstance(index, slice):
            # Normalize slice start and stop
            start = index.start if index.start is not None else 0
            stop = index.stop if index.stop is not None else self.size
            obj_ptr = self._pyobject.GetSlice(start, stop)
            ls = obj_ptr.contents.into_object()
            # Get step if provided
            if index.step is not None:
                ls = ls[:: index.step]
            return ls
        raise TypeError(f"Invalid index type: {type(index)}")

    def __setitem__(self, index: int, value: _VT) -> None:
        if isinstance(index, int):
            self._pyobject.SetItem(index.__index__(), value)
        elif isinstance(index, slice):
            if index.step is not None:
                raise ValueError("Cannot set slice with step")
            # Normalize slice start and stop
            start = index.start if index.start is not None else 0
            stop = index.stop if index.stop is not None else self.size
            self._pyobject.SetSlice(start, stop, value)
        else:
            raise TypeError(f"Invalid index type: {type(index)}")

    def __len__(self) -> int:
        return self.size

    @property
    def allocated(self) -> int:
        """Allocated size of the list."""
        return self._pyobject.allocated  # type: ignore

    @allocated.setter
    @unsafe
    def allocated(self, value: int) -> None:
        """Set the allocated size of the list."""
        self._pyobject.allocated = value

    @property
    def item(self) -> Array[ptr[PyObject[_VT]]]:
        """Array of item pointers in the list."""
        arr_type = POINTER(PyObject) * self.size
        arr = arr_type.from_address(addressof(self._pyobject.ob_item.contents))
        return arr

    @item.setter
    @unsafe
    def item(
        self, value: Array[ptr[PyObject]] | Sequence[ptr[PyObject]] | Sequence[object]
    ) -> None:
        if not isinstance(value, Array):
            value = [PyObject.try_from(v).with_ref().as_ref() for v in value]
            value = seq_to_array(value, POINTER(PyObject))
        memmove(self._pyobject.ob_item, value, sizeof(value))
