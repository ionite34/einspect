"""Parsing type hints."""
from __future__ import annotations

import ctypes
import typing
from ctypes import POINTER
from typing import Any, Protocol, Sequence, runtime_checkable

# noinspection PyProtectedMember
from _ctypes import _SimpleCData
from typing_extensions import Self

Py_ssize_t = ctypes.c_ssize_t


@runtime_checkable
class FuncPtr(Protocol):
    """Type of ctypes.pythonapi functions (ctypes._FuncPtr)."""
    restype: type | None
    argtypes: Sequence[type]

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        ...


aliases = {
    # ctypes will cast c_ssize_t to (int)
    int: Py_ssize_t,
    # ctypes will cast py_object to (object)
    object: ctypes.py_object,
    # convert hints of None (inspected as NoneType) back to None
    type(None): None,
}


def convert_type_hints(source: type, owner_cls: type) -> type | None:
    """Convert type hints to types usable for FuncPtr."""
    # Unpack optionals
    if type(source) is typing.Optional:
        source = typing.get_args(source)[0]
        return convert_type_hints(source, owner_cls)
    # For unions
    if type(source) is typing.Union:
        sources = typing.get_args(source)
        # Find first ctypes type
        for source in sources:
            if type(source) is type and issubclass(source, _SimpleCData):
                return source
        # Otherwise use first type
        source = sources[0]

    # For TypeVar, convert to py_object
    if type(source) is typing.TypeVar:
        return ctypes.py_object

    if source == Self:
        source = owner_cls

    if source in aliases:
        return aliases[source]

    # Replace with a pointer type if it's a structure
    if issubclass(source, ctypes.Structure):
        return POINTER(source)

    # For non-ctypes (and not None) types, substitute with py_object
    if not is_ctypes_type(source):
        source = ctypes.py_object

    return source


def is_ctypes_type(obj: Any) -> bool:
    """Return True if the object is a ctypes type."""
    try:
        ctypes.POINTER(obj)
        return True
    except TypeError:
        return False
