"""Function factory to create views for objects."""
from __future__ import annotations

from typing import overload, TypeVar, TYPE_CHECKING

from einspect.views.view_int import IntView
from einspect.views.view_list import ListView
from einspect.views.view_tuple import TupleView
from einspect.views.view_str import StrView
from einspect.views.view_base import View, REF_DEFAULT

if TYPE_CHECKING:
    ...


_IntType = TypeVar("_IntType", bound=int)
_StrType = TypeVar("_StrType", bound=str)
_ListType = TypeVar("_ListType", bound=list)
_TupleType = TypeVar("_TupleType", bound=tuple)
_ObjectType = TypeVar("_ObjectType", bound=object)


@overload
def view(obj: _IntType, ref: bool = REF_DEFAULT) -> IntView[_IntType]: ...


@overload
def view(obj: _ListType, ref: bool = REF_DEFAULT) -> ListView[_ListType]:
    ...


@overload
def view(obj: _TupleType, ref: bool = REF_DEFAULT) -> TupleView[_TupleType]:
    ...


@overload
def view(obj: _StrType, ref: bool = REF_DEFAULT) -> StrView[_StrType]:
    ...


@overload
def view(obj: _ObjectType, ref: bool = REF_DEFAULT) -> View[_ObjectType]:
    ...


def view(obj, ref: bool = REF_DEFAULT):
    """
    Create a view onto a Python object.

    Args:
        obj: The object to view.
        ref: If True, hold a strong reference to the object.

    Returns: A view onto the object.
    """
    if isinstance(obj, list):
        return ListView(obj, ref=ref)
    elif isinstance(obj, tuple):
        return TupleView(obj, ref=ref)
    elif isinstance(obj, int):
        return IntView(obj, ref=ref)
    elif isinstance(obj, str):
        return StrView(obj, ref=ref)
    else:
        # Base case
        return View(obj, ref=ref)


view.__getitem__ = lambda self, item: self.getitem(item)
