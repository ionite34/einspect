from __future__ import annotations

import ctypes
from ctypes import Array
from typing import Sequence, overload, TypeVar

from einspect.errors import UnsafeIndexError, UnsafeAttributeError
from einspect.structs import PyTupleObject
from einspect.utils import new_ref
from einspect.views.view_base import VarView


_T = TypeVar("_T")


class TupleView(VarView[_T], Sequence):
    _pyobject: PyTupleObject

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
                addr = self._pyobject.GetItem(self._pyobject, index)
                return addr
            except IndexError as err:
                raise IndexError(f"Index {index} out of range") from err
        elif isinstance(index, slice):
            raise NotImplementedError
        else:
            raise TypeError(f"Invalid index type: {type(index)}")

    def __setitem__(self, key: int, value: _S) -> None:
        # First use SetItem api
        try:
            # Get current item and decref
            prev_item = self._pyobject.GetItem(self._pyobject, key)
            # pythonapi.Py_DecRef(prev_item)
            # ref = ctypes.py_object(value)
            # pythonapi.Py_IncRef(ref)
            ref = new_ref(value)
            arr = self.item
            arr[key] = ref
            # self._pyobject.SetItem(self._pyobject, key, ref)
        except IndexError as err:
            if not self._unsafe:
                raise UnsafeIndexError(
                    "Setting indices beyond current size requires entering the unsafe() context."
                ) from err
            else:
                if key < 0:
                    raise IndexError(f"Index {key} out of range") from err

                # If unsafe, use direct set by creating a new array
                # noinspection PyProtectedMember
                start_addr = ctypes.addressof(self._pyobject._ob_item_0)
                # Size should be higher of the current size and the index
                size = max(self.size, key + 1)
                arr = (Py_ssize_t * size).from_address(start_addr)
                arr[key] = new_ref(value)

    def __len__(self) -> int:
        return self.size

    @property
    def item(self) -> Array[Py_ssize_t]:
        return self._pyobject.ob_item

    @item.setter
    def item(self, value: Array) -> None:
        if not self._unsafe:
            raise UnsafeAttributeError.from_attr("item")
        self._pyobject.ob_item = value
