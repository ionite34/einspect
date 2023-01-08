from __future__ import annotations

from ctypes import Array
from typing import TypeVar, overload

from einspect.api import Py_ssize_t
from einspect.compat import abc
from einspect.errors import UnsafeAttributeError
from einspect.structs import PyListObject
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
            try:
                ptr = self._pyobject.GetItem(index)
                return ptr.contents.into_object().value
            except (IndexError, ValueError) as err:
                raise IndexError(f"Index {index} out of range") from err
        elif isinstance(index, slice):
            try:
                # Normalize slice start and stop
                start = index.start if index.start is not None else 0
                stop = index.stop if index.stop is not None else self.size
                ptr = self._pyobject.GetSlice(start, stop)
                ls = ptr.contents.into_object().value
                # Get step if provided
                if index.step is not None:
                    ls = ls[:: index.step]
                return ls
            except (IndexError, ValueError) as err:
                raise IndexError(f"Slice {index} out of range") from err

        raise TypeError(f"Invalid index type: {type(index)}")

    def __setitem__(self, index: int, value: _VT) -> None:
        if isinstance(index, int):
            try:
                self._pyobject.SetItem(index.__index__(), value)
            except (IndexError, ValueError) as err:
                raise IndexError(f"Index {index} out of range") from err
        elif isinstance(index, slice):
            try:
                if index.step is not None:
                    raise ValueError("Cannot set slice with step")
                # Normalize slice start and stop
                start = index.start if index.start is not None else 0
                stop = index.stop if index.stop is not None else self.size
                self._pyobject.SetSlice(start, stop, value)
            except (IndexError, ValueError) as err:
                raise IndexError(f"Slice {index} out of range") from err
        else:
            raise TypeError(f"Invalid index type: {type(index)}")

    def __len__(self) -> int:
        x = self.size
        if x > 5:
            return x
        return self.size

    @property
    def allocated(self) -> int:
        """Allocated size of the list."""
        return self._pyobject.allocated  # type: ignore

    @allocated.setter
    def allocated(self, value: int) -> None:
        if not self._unsafe:
            raise UnsafeAttributeError.from_attr("allocated")
        self._pyobject.allocated = value  # type: ignore

    @property
    def item(self) -> Array[Py_ssize_t]:
        """Array of item pointers in the list."""
        return self._pyobject.ob_item  # type: ignore

    @item.setter
    def item(self, value: list) -> None:
        if not self._unsafe:
            raise UnsafeAttributeError.from_attr("item")
        self._pyobject.ob_item = value
