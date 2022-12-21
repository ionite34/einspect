"""Function factory to create views for objects."""
from __future__ import annotations

from types import MappingProxyType
from typing import Final, Type, TypeVar, get_args, overload

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

views_map = {
    int: IntView,
    str: StrView,
    list: ListView,
    tuple: TupleView,
}
"""Mapping of (type): (view class)."""

# Builtin types
_Str = TypeVar("_Str", bound=str)
_Int = TypeVar("_Int", bound=int)
_Float = TypeVar("_Float", bound=float)
_List = TypeVar("_List", bound=list)
_Tuple = TypeVar("_Tuple", bound=tuple)
_Dict = TypeVar("_Dict", bound=dict)

# Collection generics
_KT = TypeVar("_KT")
_VT_co = TypeVar("_VT_co", covariant=True)

# Base case
_Object = TypeVar("_Object", bound=object)


@overload
def view(obj: _Int, ref: bool = REF_DEFAULT) -> IntView[_Int]:
    ...


@overload
def view(obj: _List, ref: bool = REF_DEFAULT) -> ListView[_List]:
    ...


@overload
def view(
    obj: MappingProxyType[_KT, _VT_co], ref: bool = REF_DEFAULT
) -> MappingProxyView[_KT, _VT_co]:
    ...


@overload
def view(obj: _Dict, ref: bool = REF_DEFAULT) -> DictView[_Dict]:
    ...


@overload
def view(obj: _Tuple, ref: bool = REF_DEFAULT) -> TupleView[_Tuple]:
    ...


@overload
def view(obj: _Str, ref: bool = REF_DEFAULT) -> StrView[_Str]:
    ...


@overload
def view(obj: _Float, ref: bool = REF_DEFAULT) -> FloatView[_Float]:
    ...


@overload
def view(obj: _Object, ref: bool = REF_DEFAULT) -> View[_Object]:
    ...


def view(obj, ref: bool = REF_DEFAULT):
    """
    Create a view onto a Python object.

    Args:
        obj: The object to view.
        ref: If True, hold a strong reference to the object.

    Returns:
        A view onto the object.
    """
    if isinstance(obj, list):
        return ListView(obj, ref=ref)
    elif isinstance(obj, tuple):
        return TupleView(obj, ref=ref)
    elif isinstance(obj, MappingProxyType):
        return MappingProxyView(obj, ref=ref)
    elif isinstance(obj, dict):
        return DictView(obj, ref=ref)
    elif isinstance(obj, int):
        return IntView(obj, ref=ref)
    elif isinstance(obj, str):
        return StrView(obj, ref=ref)
    elif isinstance(obj, float):
        return FloatView(obj, ref=ref)
    return View(obj, ref=ref)
