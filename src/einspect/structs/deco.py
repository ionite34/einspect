from __future__ import annotations

import ctypes
import logging
import typing
from ctypes import POINTER, Structure
from functools import cached_property, partial
from typing import Callable, Literal, Sequence, Tuple, Type, TypeVar, overload

import typing_extensions
from typing_extensions import get_args, get_type_hints

from einspect.protocols.type_parse import (
    convert_type_hints,
    fix_ctypes_generics,
    is_ctypes_type,
)
from einspect.structs.traits import AsRef, Display
from einspect.types import NULL, Pointer, PyCFuncPtrType, _SelfPtr

__all__ = ("struct", "Struct")

# noinspection PyUnresolvedReferences, PyProtectedMember
AnnotatedAlias = typing_extensions._AnnotatedAlias

log = logging.getLogger(__name__)

_T = TypeVar("_T", bound=Type[Structure])

FieldsType = Sequence[typing.Union[Tuple[str, type], Tuple[str, type, int]]]


@overload
def struct(*, fields: FieldsType) -> Callable[[_T], _T]:
    ...


@overload
def struct(cls: _T, fields: Literal[None] = ...) -> _T:
    ...


def struct(cls: _T | None = None, fields: FieldsType | None = None):
    """Decorator to declare _fields_ on Structures via type hints."""
    # Normal decorator usage
    if cls is not None:
        return _struct(cls)

    # Usage as a decorator factory
    return partial(_struct, __fields=fields)


def _struct(cls: _T, __fields: FieldsType | None = None) -> _T:
    """Decorator to declare _fields_ on Structures via type hints."""
    # if fields provided, replace type hints with temp sentinel
    fields_overrides = {}
    for tup in __fields or ():
        f_name, f_type, *_ = tup
        f_ls = list(tup)
        # Convert SelfPtr types to POINTER(cls)
        if f_type is _SelfPtr:
            f_ls[1] = POINTER(cls)  # type: ignore

        fields_overrides[f_name] = tuple(f_ls)

    if __fields is not None:
        for tup in __fields:
            # This is to prevent errors during get_type_hints if there is an override
            cls.__annotations__[tup[0]] = None

    fields = []
    # Locals dict for type hint resolution
    hint_locals = {cls.__name__: cls}
    try:
        hints = get_type_hints(cls, None, hint_locals, include_extras=True)
    except (TypeError, NameError):
        # Normalize annotations of py_object subscripts
        fix_ctypes_generics(cls.__annotations__, cls.__name__)
        hints = get_type_hints(cls, None, hint_locals, include_extras=True)

    for name, type_hint in hints.items():
        # Use override if exists
        if f := fields_overrides.get(name):
            fields.append(f)
            continue
        # Skip actual values like _fields_
        if name.startswith("_") and name.endswith("_"):
            continue
        # Skip callables
        if type_hint == Callable:
            continue
        # Since get_type_hints also gets superclass hints, skip them
        if name not in cls.__annotations__:
            continue

        # For Annotated, directly use fields 1 and 2
        if type(type_hint) is AnnotatedAlias:
            args = get_args(type_hint)
            res = (name, *args[1:3])
            log.debug(f"Annotated: {type_hint} -> {res}")
            fields.append((name, *args[1:3]))
            continue

        type_hint = convert_type_hints(type_hint, cls)
        fields.append((name, type_hint))

    # We must only set this once as _fields_ is final
    try:
        cls._fields_ = fields
    except (TypeError, AttributeError) as err:
        raise TypeError(f"Failed to set {cls.__name__!r} _fields_, {err}") from err

    return cls


def _cast_field(field_type, value):
    """Attempt to cast value for assignment to ctypes field_type."""
    # Both Pointer types
    if issubclass(field_type, Pointer) and isinstance(value, Pointer):
        # Null case, create empty pointer
        if value is NULL:
            return field_type()
        # try to coerce Structure subclasses
        # i.e. LP_PyObject should accept LP_PyDictObject
        elif issubclass(field_type._type_, Structure) and issubclass(
            value._type_, field_type._type_
        ):
            return ctypes.cast(value, field_type)

    # PYFUNCTYPE
    if isinstance(field_type, PyCFuncPtrType):
        # For null, return new empty function pointer
        if value is NULL:
            return field_type()
        # For function, cast with PYFUNCTYPE
        elif not is_ctypes_type(value):
            return field_type(value)

    return value


class UnionMeta(type(ctypes.Union)):
    def __init__(self, name, bases, mapping, **kwargs) -> None:
        super().__init__(name, bases, mapping, **kwargs)
        _struct(self)  # type: ignore


class StructMeta(type(ctypes.Structure)):
    def __init__(self, name, bases, mapping, **kwargs) -> None:
        super().__init__(name, bases, mapping, **kwargs)
        _struct(self)  # type: ignore


class Union(ctypes.Union, AsRef, Display, metaclass=UnionMeta):
    """Defines a ctypes.Union subclass using type hints."""

    _fields_: typing.List[typing.Union[Tuple[str, type], Tuple[str, type, int]]]


class Struct(Structure, AsRef, Display, metaclass=StructMeta):
    """Defines a ctypes.Structure subclass using type hints."""

    _fields_: typing.List[typing.Union[Tuple[str, type], Tuple[str, type, int]]]

    @cached_property
    def _fields_map_(self) -> dict[str, tuple[str, type] | tuple[str, type, int]]:
        """Returns a dict of field name to field tuple. Includes inherited fields."""
        super_fields = super()._fields_ if hasattr(super(), "_fields_") else {}
        return {**super_fields, **{f[0]: f for f in self._fields_}}

    def __setattr__(self, key, value):
        # Overrides for field assignments
        if key in self._fields_map_:
            # Get the field type
            field_type = self._fields_map_[key][1]
            # Attempt to cast value to field type
            value = _cast_field(field_type, value)

        super().__setattr__(key, value)
