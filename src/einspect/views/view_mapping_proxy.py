from __future__ import annotations

from types import MappingProxyType
from typing import TypeVar

from einspect.compat import abc
from einspect.structs import PyDictObject
from einspect.structs.mapping_proxy import MappingProxyObject
from einspect.views.unsafe import unsafe
from einspect.views.view_base import REF_DEFAULT, View

__all__ = ("MappingProxyView",)

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class MappingProxyView(View[MappingProxyType, _KT, _VT], abc.MutableMapping[_KT, _VT]):
    _pyobject: MappingProxyObject[_KT, _VT]

    def __init__(
        self, obj: MappingProxyType[_KT, _VT], ref: bool = REF_DEFAULT
    ) -> None:
        super().__init__(obj, ref)

    def __len__(self) -> int:
        return dict.__len__(self.mapping)

    def __iter__(self) -> abc.Iterator[_KT]:
        return dict.__iter__(self.mapping)

    def __getitem__(self, __k: _KT) -> _VT:
        return dict.__getitem__(self.mapping, __k)

    def __setitem__(self, __k: _KT, __v: _VT) -> None:
        return dict.__setitem__(self.mapping, __k, __v)

    def __delitem__(self, __v: _KT) -> None:
        return dict.__delitem__(self.mapping, __v)

    @property
    def mapping(self) -> dict[_KT, _VT]:
        """Return `MappingProxyObject.mapping`, casted to `dict`."""
        return self._pyobject.mapping.contents.into_object()

    @mapping.setter
    @unsafe
    def mapping(self, value: dict[_KT, _VT]) -> None:
        self._pyobject.mapping = PyDictObject.from_object(value).with_ref().as_ref()
