from __future__ import annotations

from collections.abc import MutableSequence
from ctypes import Array
from typing import Iterable, SupportsIndex, TypeVar, Union, overload

from einspect.api import Py_ssize_t
from einspect.errors import UnsafeError
from einspect.structs.py_unicode import (
    Kind,
    PyASCIIObject,
    PyCompactUnicodeObject,
    PyUnicodeObject,
    State,
)
from einspect.views.unsafe import unsafe
from einspect.views.view_base import REF_DEFAULT, View

__all__ = ("StrView",)

_T = TypeVar("_T")


class StrView(View[str, None, None], MutableSequence):
    _pyobject: Union[PyASCIIObject, PyCompactUnicodeObject, PyUnicodeObject]

    def __init__(self, obj: str, ref: bool = REF_DEFAULT) -> None:
        """View a Python string object."""
        super().__init__(obj, ref)
        # Start with PyASCIIObject, check if we can use a more specific type
        self._narrow_type()

    def _narrow_type(self) -> None:
        # Narrow to a more specific unicode type if possible
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
        # Use a temp list for the slice calculation
        temp = list(self._pyobject.into_object())
        temp[index] = value
        # Combine to str
        target = "".join(temp)

        # See if resizing is safe
        if target.__sizeof__() > self.mem_allocated and not self._unsafe:
            raise UnsafeError(
                "setitem required str to be resized beyond current memory allocation."
                " Enter an unsafe context to allow this."
            )

        # Since the struct type might change, use a memmove
        v = StrView(target, ref=False)
        with self.unsafe(), v.unsafe():
            v.move_to(self)
        self._narrow_type()

        # On modifications, unintern the string
        self._pyobject.interned = 0

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

        # See if resizing is safe
        if target.__sizeof__() > self.mem_allocated and not self._unsafe:
            raise UnsafeError(
                "setitem required str to be resized beyond current memory allocation."
                " Enter an unsafe context to allow this."
            )

        # Since the struct type might change, use a memmove
        v = StrView(target, ref=False)
        with self.unsafe(), v.unsafe():
            v.move_to(self)
        self._narrow_type()

        # On modifications, unintern the string
        self._pyobject.interned = 0

    def insert(self, index: SupportsIndex, value: str) -> None:
        """Insert object before index."""
        index = index.__index__()
        # Use a temp list for the slice calculation
        temp = list(self._pyobject.into_object())
        temp.insert(index, value)
        # Combine to str
        target = "".join(temp)

        # See if resizing is safe
        if target.__sizeof__() > self.mem_allocated and not self._unsafe:
            raise UnsafeError(
                "insert required str to be resized beyond current memory allocation."
                " Enter an unsafe context to allow this."
            )

        # Since the struct type might change, use a memmove
        v = StrView(target, ref=False)
        with self.unsafe(), v.unsafe():
            v.move_to(self)
        self._narrow_type()

        # On modifications, unintern the string
        self._pyobject.interned = 0

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
