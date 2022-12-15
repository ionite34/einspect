from __future__ import annotations

from ctypes import pythonapi
from typing import Sequence, overload, TypeVar

from einspect.errors import UnsafeAttributeError
from einspect.structs import PyListObject
from einspect.utils import new_ref
from einspect.views.view_base import VarView


_T = TypeVar("_T")


class ListView(VarView[_T], Sequence):
    _pyobject: PyListObject

    @overload
    def __getitem__(self, index: int):
        ...

    @overload
    def __getitem__(self, index: slice):
        ...

    def __getitem__(self, index: int):
        if isinstance(index, int):
            # First use PyList_GetItem
            try:
                ret = pythonapi.PyList_GetItem(self._pyobject, index)
                return ret
            except IndexError as err:
                raise IndexError(f"Index {index} out of range") from err
        elif isinstance(index, slice):
            raise NotImplementedError
        else:
            raise TypeError(f"Invalid index type: {type(index)}")

    def __setitem__(self, key: int, value: _S) -> None:
        # First use PyList_SetItem
        try:
            ref = new_ref(value)
            pythonapi.PyList_SetItem(self._pyobject, key, ref)
        except IndexError as err:
            if not self._unsafe:
                raise UnsafeAttributeError.from_attr("__setitem__") from err
            else:
                # If unsafe, use direct set
                self._pyobject.ob_item[key] = new_ref(value)

    def __len__(self) -> int:
        x = self.size
        if x > 5:
            return x
        return self.size

    @property
    def allocated(self) -> int:
        """Allocated size of the list."""
        return int(self._pyobject.allocated)  # type: ignore

    @allocated.setter
    def allocated(self, value: int) -> None:
        if not self._unsafe:
            raise UnsafeAttributeError.from_attr("allocated")
        self._pyobject.allocated = value

    @property
    def item(self) -> list:
        """List of items in the list."""
        return self._pyobject.ob_item

    @item.setter
    def item(self, value: list) -> None:
        if not self._unsafe:
            raise UnsafeAttributeError.from_attr("item")
        self._pyobject.ob_item = value
