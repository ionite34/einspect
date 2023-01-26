"""Parsing type hints."""
from __future__ import annotations

import ctypes
import logging
import re
import typing
from ctypes import POINTER
from typing import Any, Protocol, Sequence, TypeVar, get_origin, runtime_checkable

from typing_extensions import Self

log = logging.getLogger(__name__)

Py_ssize_t = ctypes.c_ssize_t


@runtime_checkable
class FuncPtr(Protocol):
    """Type of ctypes.pythonapi functions (ctypes._FuncPtr)."""

    restype: type | None
    argtypes: Sequence[type]

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        ...  # pragma: no cover


aliases = {
    # ctypes will cast c_ssize_t to (int)
    int: Py_ssize_t,
    # ctypes will cast py_object to (object)
    object: ctypes.py_object,
    type: ctypes.py_object,
    # convert hints of None (inspected as NoneType) back to None
    type(None): None,
}

# ctypes generics to replace
RE_PY_OBJECT = re.compile(r"^(py_object)(\[(.*)])$")
RE_POINTER = re.compile(r"^(pointer)(\[(.*)])$")
RE_ANNOTATED = re.compile(r"^(Annotated)(\[(.*)])$")


def fix_ctypes_generics(
    type_hints: dict[str, str | type], cls_name: str | None = None
) -> None:
    """
    Replace some unresolvable ctypes hints in __annotations__.

    Args:
        type_hints: The __annotations__ dict to fix.
        cls_name: The name of the class to fix.
    """
    for name, hint in type_hints.items():
        if not isinstance(hint, str):
            continue
        # For Annotated c_void_p, directly set it here to avoid name errors
        if m := RE_ANNOTATED.match(hint):
            inner = m.group(3)
            # Split from right to first ,
            _, last = inner.rsplit(",", 1)
            log.debug(last)
            if last.strip() == "c_void_p":
                log.debug("RE_ANNOTATED Set: %r -> %r", name, ctypes.c_void_p)
                type_hints[name] = ctypes.c_void_p

        # Keep py_object and discard subscript
        if m := RE_PY_OBJECT.match(hint):
            log.debug("Source: %r Match: %r", hint, m)
            base = hint.replace(m.group(2), "")
            type_hints[name] = base
            log.debug("Replacing %r with %r", hint, base)
        # For pointer, replace with POINTER
        if m := RE_POINTER.match(hint):
            # Get inner of []
            base = m.group(3)
            # Discard any other generics
            base = base.split("[")[0]
            type_hints[name] = base
            log.debug("Replacing %r with %r", hint, base)


def convert_type_hints(source: type, owner_cls: type) -> type | None:
    """Convert type hints to types usable for FuncPtr."""
    # Unpack optionals
    if hasattr(source, "__origin__"):
        if get_origin(source) == typing.Union:
            source = typing.get_args(source)[0]
            return convert_type_hints(source, owner_cls)

    # Convert TypeVar and Type to py_object
    if (type(source) is TypeVar) or get_origin(source) is type:
        return ctypes.py_object

    if source == Self:
        source = owner_cls

    # Get base of generic alias
    # noinspection PyUnresolvedReferences, PyProtectedMember
    if isinstance(source, typing._GenericAlias):
        source = get_origin(source)

    if source in aliases:
        return aliases[source]

    # Replace with a pointer type if it's a structure
    try:
        if issubclass(source, ctypes.Structure):
            return POINTER(source)
    except TypeError as e:
        raise TypeError(
            f"Failed to convert type hint ({type(source)}) {source!r} for {owner_cls!r} -> {e}"
        ) from e

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
