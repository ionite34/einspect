from __future__ import annotations

from collections.abc import Callable, MutableSequence, Sequence
from ctypes import Array, addressof, c_void_p, memmove, sizeof
from typing import Any, SupportsIndex, TypeVar, overload

from einspect.api import PTR_SIZE
from einspect.errors import UnsafeError
from einspect.structs import PyListObject, PyObject, PyTupleObject
from einspect.types import SupportsLessThan, ptr
from einspect.views.unsafe import unsafe
from einspect.views.view_base import VarView

__all__ = ("TupleView",)

_T = TypeVar("_T")


def can_resize(view: TupleView, target: int) -> bool:
    """Check if the tuple can be resized to `target` length."""
    if target <= view.size:
        return True

    current_size = view.mem_size
    delta = (target - view.size) * sizeof(c_void_p)
    return current_size + delta <= view.mem_allocated


class TupleView(VarView[tuple, None, _T], MutableSequence):
    _pyobject: PyTupleObject[_T]

    def __init__(self, obj: tuple[_T, ...] | tuple, ref: bool = True) -> None:
        """View a tuple object."""
        super().__init__(obj, ref)

    def __len__(self) -> int:
        return self.size

    @overload
    def __getitem__(self, index: SupportsIndex) -> _T:
        ...

    @overload
    def __getitem__(self, index: slice) -> tuple[_T]:
        ...

    def __getitem__(self, index: SupportsIndex | slice) -> _T | tuple[_T]:
        if isinstance(index, slice):
            start = index.start if index.start is not None else 0
            stop = index.stop if index.stop is not None else self.size
            ref = self._pyobject.GetSlice(start, stop)
            return ref.contents.into_object()
        else:
            index = index.__index__()
            ob_size = self._pyobject.ob_size
            pos_index = index if index >= 0 else ob_size + index
            py_obj = self._pyobject.GetItem(pos_index).contents
            return py_obj.into_object()

    def __setitem__(self, index: SupportsIndex | slice, value: Any) -> None:
        if isinstance(index, slice):
            # Use a temp list for the slice calculation
            temp = list(self)
            temp[index] = value
            # Check the size diff
            diff = len(temp) - self.size

            # Try to resize
            if not can_resize(self, self.size + diff) and not self._unsafe:
                raise UnsafeError(
                    "setting slice required tuple to be resized beyond current memory allocation."
                    " Enter an unsafe context to allow this."
                )
            self._pyobject.ob_size = len(temp)
            # Set the items
            for i, item in enumerate(temp):
                self[i] = item
        else:
            index = index.__index__()
            obj = PyObject.from_object(value)
            obj.IncRef()
            self.item[index] = obj.as_ref()

    @overload
    def __delitem__(self, index: SupportsIndex) -> None:
        ...

    @overload
    def __delitem__(self, index: slice) -> None:
        ...

    def __delitem__(self, index: SupportsIndex | slice) -> None:
        if isinstance(index, slice):
            r = range(self.size)[index]
            for i in reversed(r):
                del self[i]
        else:
            index = index.__index__()
            ob_size = self._pyobject.ob_size
            # Check index
            pos_index = index if index >= 0 else ob_size + index
            if pos_index >= ob_size:
                raise IndexError("tuple assignment index out of range")
            # Get the item to DecRef it
            item = self._pyobject.ob_item[index]
            if item:  # Ignore if already null pointer
                item.contents.DecRef()
            # Set the item to null
            self._pyobject.ob_item[index] = ptr[PyObject]()
            # Shift items unless this is the last item
            if pos_index != ob_size - 1:
                src = addressof(self._pyobject.ob_item[pos_index + 1])
                dst = addressof(item)
                size = (ob_size - pos_index - 1) * sizeof(c_void_p)
                memmove(dst, src, size)
            # Reduce size
            self._pyobject.ob_size -= 1

    def pop(self, index: SupportsIndex | None = None) -> _T:
        """
        Remove and return item at index (default last).

        Raises IndexError if tuple is empty or index is out of range.
        """
        index = index.__index__() if index is not None else -1
        if self.size == 0:
            raise IndexError("pop from empty tuple")
        try:
            return super().pop(index)
        except IndexError:
            raise IndexError("pop index out of range") from None

    def insert(self, index: SupportsIndex, value: _T) -> None:
        """Insert object before index."""
        index = index.__index__()
        # Normalize index
        ob_size = self._pyobject.ob_size
        pos_index = index if index >= 0 else ob_size + index
        # If below 0, use 0, if above size, use size
        norm_index = max(0, min(pos_index, ob_size))

        # Resize
        if not can_resize(self, self.size + 1) and not self._unsafe:
            raise UnsafeError(
                "insert required tuple to be resized beyond current memory allocation."
                " Enter an unsafe context to allow this."
            )
        self._pyobject.ob_size += 1

        # Shift items unless this is the last item
        if norm_index != ob_size:
            src = addressof(self._pyobject.ob_item[norm_index])
            dst = src + sizeof(c_void_p)
            size = (ob_size - norm_index) * sizeof(c_void_p)
            memmove(dst, src, size)

        # Set the item
        self._pyobject.ob_item[norm_index] = PyObject.from_object(value).as_ref()

    def sort(
        self,
        *,
        key: Callable[[str], SupportsLessThan] | None = None,
        reverse: bool = False,
    ) -> None:
        """
        Sort the tuple in ascending order and return None.

        The sort is in-place (i.e. the tuple itself is modified) and stable
        (i.e. the order of two equal elements is maintained).

        If a key function is given, apply it once to each tuple item and sort them,
        ascending or descending, according to their function values.

        The reverse flag can be set to sort in descending order.
        """
        # Skip empty
        if self._pyobject.ob_size == 0:
            return None
        temp = sorted(self._pyobject.into_object(), key=key, reverse=reverse)
        temp_obj = PyListObject.from_object(temp)
        assert temp_obj.ob_size == self._pyobject.ob_size
        # Move the references
        memmove(
            addressof(self._pyobject.ob_item),
            addressof(temp_obj.ob_item.contents),
            self._pyobject.ob_size * PTR_SIZE,
        )

    @property
    def item(self) -> Array[ptr[PyObject[_T]]]:
        """The `ob_item` array of PyObject pointers."""
        return self._pyobject.ob_item

    @item.setter
    @unsafe
    def item(
        self, value: Array[ptr[PyObject]] | Sequence[ptr[PyObject]] | Sequence[object]
    ) -> None:
        """Set the `ob_item` array of PyObject pointers."""
        if not isinstance(value, Array):
            value = [PyObject.try_from(v).with_ref().as_ref() for v in value]
        self._pyobject.ob_item = value
