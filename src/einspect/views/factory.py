"""Function factory to create views for objects."""
from __future__ import annotations

from collections.abc import Callable
from types import BuiltinFunctionType, FunctionType, MappingProxyType
from typing import Any, Final, TypeVar, overload

from einspect.views import CFunctionView
from einspect.views.view_base import REF_DEFAULT, View
from einspect.views.view_bool import BoolView
from einspect.views.view_dict import DictView
from einspect.views.view_float import FloatView
from einspect.views.view_function import FunctionView
from einspect.views.view_int import IntView
from einspect.views.view_list import ListView
from einspect.views.view_mapping_proxy import MappingProxyView
from einspect.views.view_set import SetView
from einspect.views.view_str import StrView
from einspect.views.view_tuple import TupleView
from einspect.views.view_type import TypeView

__all__ = ("view",)

VIEW_TYPES: Final[dict[type, type[View]]] = {
    object: View,
    type: TypeView,
    int: IntView,
    bool: BoolView,
    float: FloatView,
    str: StrView,
    list: ListView,
    tuple: TupleView,
    set: SetView,
    dict: DictView,
    MappingProxyType: MappingProxyView,
    FunctionType: FunctionView,
    BuiltinFunctionType: CFunctionView,
}
"""Mapping of (type): (view class)."""

# Collection generics
_KT = TypeVar("_KT")
_VT = TypeVar("_VT")

# TypeView
_Type = TypeVar("_Type", bound=type)

# Base case
_T = TypeVar("_T")


@overload
def view(obj: int, ref: bool = REF_DEFAULT) -> IntView:
    ...


@overload
def view(obj: bool, ref: bool = REF_DEFAULT) -> BoolView:
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
def view(obj: set[_VT], ref: bool = REF_DEFAULT) -> SetView[_VT]:
    ...


@overload
def view(obj: tuple[_VT, ...], ref: bool = REF_DEFAULT) -> TupleView[_VT]:
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
def view(obj: _Type, ref: bool = REF_DEFAULT) -> TypeView[_Type]:
    ...


# Ideally we'd have separate overloads for builtin vs user-defined functions,
# but typeshed only defines builtin functions as Callable.
@overload
def view(
    obj: BuiltinFunctionType | FunctionType | Callable, ref: bool = REF_DEFAULT
) -> FunctionView | CFunctionView:
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

    # Fallback to subclasses
    for obj_type, view_type in reversed([*VIEW_TYPES.items()]):
        if isinstance(obj, obj_type):
            return view_type(obj, ref=ref)

    # Shouldn't reach here since we will at least match isinstance object
    raise TypeError(f"Cannot create view for {obj_type}")  # pragma: no cover
