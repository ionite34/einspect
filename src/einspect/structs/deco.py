from __future__ import annotations

import logging
from ctypes import Structure
from typing import Callable, Type, TypeVar, get_type_hints

from einspect.protocols.type_parse import convert_type_hints, fix_ctypes_generics

log = logging.getLogger(__name__)

_T = TypeVar("_T", bound=Type[Structure])


def struct(cls: _T) -> _T:
    """Decorator to declare _fields_ on Structures via type hints."""
    fields = []
    try:
        hints = get_type_hints(cls)
    except TypeError:
        # Normalize annotations of py_object subscripts
        fix_ctypes_generics(cls.__annotations__)
        hints = get_type_hints(cls)

    for name, type_hint in hints.items():
        # Skip actual values like _fields_
        if name.startswith("_") and name.endswith("_"):
            continue
        # Skip callables
        if type_hint == Callable:
            continue
        # Since get_type_hints also gets superclass hints, skip them
        if name not in cls.__annotations__:
            continue

        type_hint = convert_type_hints(type_hint, cls)

        # Check if there is a real class-attribute assigned
        if hasattr(cls, name):
            value = getattr(cls, name)
            # use it as the default value
            fields.append((name, type_hint, value))
        else:
            # otherwise no default value
            fields.append((name, type_hint))

    # We have to only set this once as _fields_ is final
    try:
        cls._fields_ = fields
    except TypeError as e:
        raise TypeError(
            f"Failed to set _fields_ on {cls.__name__}: {fields}"
        ) from e

    return cls
