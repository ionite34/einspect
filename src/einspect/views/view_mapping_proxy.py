from __future__ import annotations

from collections.abc import Iterator, MutableMapping
from types import MappingProxyType
from typing import TypeVar

from einspect.structs.mapping_proxy import MappingProxyObject
from einspect.structs.py_dict import PyDictObject
from einspect.views import REF_DEFAULT
from einspect.views.unsafe import unsafe
from einspect.views.view_base import View

_KT = TypeVar("_KT")
_VT_co = TypeVar("_VT_co", covariant=True)


class MappingProxyView(View[MappingProxyType[_KT, _VT_co]], MutableMapping[_KT, _VT_co]):
    _pyobject: MappingProxyObject[_KT, _VT_co]

    def __init__(self, obj: MappingProxyType[_KT, _VT_co], ref: bool = REF_DEFAULT) -> None:
        super().__init__(obj, ref)

    def __len__(self) -> int:
        return dict.__len__(self.mapping)

    def __iter__(self) -> Iterator[_KT]:
        return dict.__iter__(self.mapping)

    def __getitem__(self, __k: _KT) -> _VT_co:
        return dict.__getitem__(self.mapping, __k)

    def __setitem__(self, __k: _KT, __v: _VT_co) -> None:
        return dict.__setitem__(self.mapping, __k, __v)

    def __delitem__(self, __v: _KT) -> None:
        return dict.__delitem__(self.mapping, __v)

    @property
    def mapping(self) -> dict[_KT, _VT_co]:
        return self._pyobject.mapping.contents.into_object().value

    @mapping.setter
    def mapping(self, value: dict[_KT, _VT_co]) -> None:
        self._pyobject.mapping = value
