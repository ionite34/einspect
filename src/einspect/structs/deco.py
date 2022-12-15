from __future__ import annotations

from ctypes import Structure
from typing import get_type_hints, TypeVar, Type

from einspect.api import Py_ssize_t

_T = TypeVar("_T", bound=Type[Structure])

# Map of types hints that will be converted by @struct
types_map = {
    int: Py_ssize_t,
}


def struct(cls: _T) -> _T:
    """Decorator to declare _fields_ on Structures via type hints."""
    fields = []
    for name, type_hint in get_type_hints(cls).items():
        # Skip actual values like _fields_
        if name.startswith("_") and name.endswith("_"):
            continue
        # Since get_type_hints also gets superclass hints, skip them
        if name not in cls.__annotations__:
            continue
        # Convert type hint if needed
        if type_hint in types_map:
            type_hint = types_map[type_hint]

        # Check if there is a real class-attribute assigned
        if hasattr(cls, name):
            value = getattr(cls, name)
            # use it as the default value
            fields.append((name, type_hint, value))
        else:
            # otherwise no default value
            fields.append((name, type_hint))

    # We have to only set this once as _fields_ is final
    cls._fields_ = fields

    return cls
