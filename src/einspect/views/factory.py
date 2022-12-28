"""Function factory to create views for objects."""
from __future__ import annotations

from types import MappingProxyType
from typing import Final, Type, TypeVar, overload, Any

from einspect.views import REF_DEFAULT
from einspect.views.view_base import View
from einspect.views.view_dict import DictView
from einspect.views.view_float import FloatView
from einspect.views.view_int import IntView
from einspect.views.view_list import ListView
from einspect.views.view_mapping_proxy import MappingProxyView
from einspect.views.view_str import StrView
from einspect.views.view_tuple import TupleView

__all__ = ("view",)

VIEW_TYPES: Final[dict[type, Type[View]]] = {
    int: IntView,
    float: FloatView,
    str: StrView,
    list: ListView,
    tuple: TupleView,
    dict: DictView,
    MappingProxyType: MappingProxyView,
}
"""Mapping of (type): (view class)."""

# Collection generics
_KT = TypeVar("_KT")
_VT = TypeVar("_VT")

# Base case
_T = TypeVar("_T")


@overload
def view(obj: int, ref: bool = REF_DEFAULT) -> IntView:
    ...


@overload
def view(obj: list[_VT], ref: bool = REF_DEFAULT) -> ListView[_VT]:
    ...


@overload
def view(
        obj: MappingProxyType[_KT, _VT], ref: bool = REF_DEFAULT
) -> MappingProxyView[_KT, _VT]:
    ...


@overload
def view(obj: dict[_KT, _VT], ref: bool = REF_DEFAULT) -> DictView[_KT, _VT]:
    ...


@overload
def view(obj: tuple[_T, ...], ref: bool = REF_DEFAULT) -> TupleView[_T]:
    ...


@overload
def view(obj: tuple, ref: bool = REF_DEFAULT) -> TupleView[Any]:
    ...


@overload
def view(obj: str, ref: bool = REF_DEFAULT) -> StrView:
    ...


@overload
def view(obj: float, ref: bool = REF_DEFAULT) -> FloatView:
    ...


@overload
def view(obj: _T, ref: bool = REF_DEFAULT) -> View[_T]:
    ...


def view(obj, ref: bool = REF_DEFAULT):
    """
    Create a view onto a Python object.

    Args:
        obj: The object to view.
        ref: If True, hold a reference to the object.

    Returns:
        A view onto the object.
    """
    obj_type = type(obj)

    if obj_type in VIEW_TYPES:
        return VIEW_TYPES[obj_type](obj, ref=ref)

    return View(obj, ref=ref)
