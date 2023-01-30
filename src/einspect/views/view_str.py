from __future__ import annotations

from collections.abc import Callable, MutableSequence
from ctypes import Array
from typing import Iterable, SupportsIndex, TypeVar, Union, overload

from einspect.api import Py_ssize_t
from einspect.errors import UnsafeError
from einspect.structs import (
    Kind,
    PyASCIIObject,
    PyCompactUnicodeObject,
    PyUnicodeObject,
    State,
)
from einspect.types import SupportsLessThan
from einspect.views.unsafe import unsafe
from einspect.views.view_base import REF_DEFAULT, View

__all__ = ("StrView",)

_T = TypeVar("_T")


def _check_resize(v: StrView, target: int, method: str) -> None:
    """
    Check if the string can be resized to `target` size.

    Raises:
        UnsafeError: If the string cannot be resized, and not in an unsafe context.
    """
    # See if resizing is safe
    if target > v.mem_allocated and not v._unsafe:
        raise UnsafeError(
            f"string {method} required {target} bytes, beyond current"
            f" allocated memory of {v.mem_allocated} bytes."
            " Enter an unsafe context to allow this."
        )


def _str_move(v: StrView, target: str) -> None:
    """Move the string to a new location."""
    # Since the struct type might change, use a memmove
    target_v = StrView(target, ref=False)
    with target_v.unsafe():
        target_v.move_to(v)
    v._narrow_type()
    # On modifications, unintern the string
    v._pyobject.interned = 0


class StrView(View[str, None, None], MutableSequence):
    _pyobject: Union[PyASCIIObject, PyCompactUnicodeObject, PyUnicodeObject]

    def __init__(self, obj: str, ref: bool = REF_DEFAULT) -> None:
        """View a string object."""
        super().__init__(obj, ref)
        # Start with PyASCIIObject, check if we can use a more specific type
        self._narrow_type()

    def _narrow_type(self) -> None:
        """Narrow to a more specific unicode type if possible."""
        if self._pyobject.compact:
            if self._pyobject.ascii:
                self._pyobject = self._pyobject.astype(PyASCIIObject)
            else:
                self._pyobject = self._pyobject.astype(PyCompactUnicodeObject)
        else:
            self._pyobject = self._pyobject.astype(PyUnicodeObject)

    def __len__(self) -> int:
        return self._pyobject.GetLength()

    @overload
    def __getitem__(self, index: int) -> str:
        ...

    @overload
    def __getitem__(self, index: slice) -> str:
        ...

    def __getitem__(self, index: int | slice) -> str:
        return str.__getitem__(self.base, index)

    @overload
    def __setitem__(self, index: int, value: str) -> None:
        ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[str]) -> None:
        ...

    def __setitem__(self, index: int | slice, value: str | Iterable[str]) -> None:
        if not isinstance(index, slice):
            index = index.__index__()
            if len(value) > 1:
                raise ValueError(
                    "cannot set integer indices with string of length > 1, use a slice instead."
                )
        # Use a temp list for the slice calculation
        temp = list(self._pyobject.into_object())
        temp[index] = value
        # Combine to str
        target = "".join(temp)

        # See if resizing is safe, then move the string
        _check_resize(self, target.__sizeof__(), "setitem")
        _str_move(self, target)

    @overload
    def __delitem__(self, index: int) -> None:
        ...

    @overload
    def __delitem__(self, index: slice) -> None:
        ...

    def __delitem__(self, index: int) -> None:
        # Use a temp list for the slice calculation
        temp = list(self._pyobject.into_object())
        del temp[index]
        # Combine to str
        target = "".join(temp)
        # See if resizing is safe, then move the string
        _check_resize(self, target.__sizeof__(), "delitem")
        _str_move(self, target)

    def insert(self, index: SupportsIndex, value: str) -> None:
        """Insert object before index."""
        index = index.__index__()
        # Use a temp list for the slice calculation
        temp = list(self._pyobject.into_object())
        temp.insert(index, value)
        # Combine to str
        target = "".join(temp)
        # See if resizing is safe, then move the string
        _check_resize(self, target.__sizeof__(), "insert")
        _str_move(self, target)

    def remove(self, value: str) -> None:
        """
        Remove first occurrence of substring value.

        Raises ValueError if the value is not present.
        """
        # Equivalent to str.replace(value, "", 1)
        target = str.replace(self._pyobject.into_object(), value, "", 1)
        # See if resizing is safe (should always be safe but check anyway)
        _check_resize(self, target.__sizeof__(), "remove")
        _str_move(self, target)

    def sort(
        self,
        *,
        key: Callable[[str], SupportsLessThan] | None = None,
        reverse: bool = False,
    ) -> None:
        """
        Sort the string in ascending order and return None.

        The sort is in-place (i.e. the string itself is modified) and stable
        (i.e. the order of two equal elements is maintained).

        If a key function is given, apply it once to each character and sort them,
        ascending or descending, according to their function values.

        The reverse flag can be set to sort in descending order.
        """
        # Skip empty
        if not self._pyobject.length:
            return None
        temp = list(self._pyobject.into_object())
        temp.sort(key=key, reverse=reverse)
        # Combine to str
        target = "".join(temp)
        # See if resizing is safe, then move the string
        _check_resize(self, target.__sizeof__(), "sort")
        _str_move(self, target)

    @property
    def length(self) -> int:
        return self._pyobject.length

    @length.setter
    def length(self, value: int) -> None:
        self._pyobject.length = value

    @property
    def hash(self) -> int:
        return self._pyobject.hash

    @hash.setter
    @unsafe
    def hash(self, value: int) -> None:
        self._pyobject.hash = value

    @property
    def interned(self) -> State:
        return State(self._pyobject.interned)

    @interned.setter
    def interned(self, value: State | int) -> None:
        self._pyobject.interned = value

    @property
    def kind(self) -> Kind:
        return Kind(self._pyobject.kind)

    @kind.setter
    def kind(self, value: Kind | int) -> None:
        self._pyobject.kind = value

    @property
    def buffer(self) -> Array[Py_ssize_t]:
        return self._pyobject.buffer
