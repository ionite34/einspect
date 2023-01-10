from __future__ import annotations

import logging
from ctypes import Structure
from functools import partial
from typing import Callable, Literal, Sequence, Tuple, Type, TypeVar, Union, overload

# noinspection PyUnresolvedReferences, PyProtectedMember
from typing_extensions import _AnnotatedAlias, get_args, get_type_hints

from einspect.protocols.type_parse import convert_type_hints, fix_ctypes_generics

log = logging.getLogger(__name__)

_T = TypeVar("_T", bound=Type[Structure])

FieldsType = Sequence[Union[Tuple[str, type], Tuple[str, type, int]]]

_TYPE_REPLACED = object()


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
    fields_overrides = {tup[0]: tup for tup in __fields or ()}
    if __fields is not None:
        for tup in __fields:
            # This is to prevent errors during get_type_hints if there is an override
            cls.__annotations__[tup[0]] = None

    fields = []
    try:
        hints = get_type_hints(cls, include_extras=True)
    except TypeError:
        # Normalize annotations of py_object subscripts
        fix_ctypes_generics(cls.__annotations__)
        hints = get_type_hints(cls, include_extras=True)

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
        if type(type_hint) is _AnnotatedAlias:
            args = get_args(type_hint)
            res = (name, *args[1:3])
            log.debug(f"Annotated: {type_hint} -> {res}")
            fields.append((name, *args[1:3]))
            continue

        type_hint = convert_type_hints(type_hint, cls)
        fields.append((name, type_hint))

    # We have to only set this once as _fields_ is final
    try:
        cls._fields_ = fields
    except TypeError as e:
        raise TypeError(f"Failed to set _fields_ on {cls.__name__}: {fields}") from e

    return cls
