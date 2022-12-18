"""Decorator protocols for binding class properties."""
from __future__ import annotations

import ctypes
import logging
import typing
from collections.abc import Callable, Sequence
from ctypes import POINTER
from functools import partial
from types import MethodType
from typing import (Any, Protocol, Type, TypeVar, get_type_hints,
                    runtime_checkable)

from typing_extensions import Self

from einspect.api import Py_ssize_t

log = logging.getLogger(__name__)

RES_TYPE_DEFAULT = ctypes.c_int
ARG_TYPES_DEFAULT = (ctypes.py_object,)


@runtime_checkable
class FuncPointer(Protocol):
    restype: Any
    argtypes: Sequence[type]

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        ...


_F = TypeVar("_F", bound=typing.Callable[[Any], FuncPointer])
_R = TypeVar("_R")
_CT = TypeVar("_CT", bound=ctypes.Structure)

aliases = {
    int: Py_ssize_t,
    object: ctypes.py_object,
}


def cast_type_aliases(source: type[Any], owner_cls: type) -> type:
    """Cast some aliases for types."""
    if source == Self:
        source = owner_cls

    if source in aliases:
        return aliases[source]

    # Replace with a pointer type if it's a structure
    if issubclass(source, ctypes.Structure):
        return POINTER(source)

    return source


def bind_api(py_api: FuncPointer) -> Callable[[_F], _F]:
    """Decorator to bind a function to a ctypes function pointer."""
    return partial(delayed_bind, py_api)


# noinspection PyPep8Naming
class delayed_bind(property):
    def __init__(self, py_api: FuncPointer, func: _F):
        super().__init__()
        self.func = func
        self.__doc__ = func.__doc__

        self.py_api = py_api

        self.attrname: str | None = None
        self.restype = None
        self.argtypes = None
        self.func_set = False

    def _get_defining_type_hints(self, cls: type) -> tuple[Sequence[type], type]:
        """Return the type hints for the attribute we're bound to, or None if it's not defined."""
        # Get the function type hints
        hints = get_type_hints(self.func)
        log.debug(f"Found type hints for {self.attrname!r}: {hints}")
        res_t = hints.pop("return", None)
        arg_t = list(hints.values())

        # Disallow any missing type hints
        if None in arg_t or res_t is None:
            raise TypeError(
                "Cannot resolve bind function type hints. "
                "Please provide them explicitly."
            )

        if res_t is not None:
            res_t = cast_type_aliases(res_t, cls)
            # Replace with None if NoneType
            res_t = None if isinstance(None, res_t) else res_t
        # Insert current class type as first argument
        arg_t.insert(0, cls)
        arg_t = [cast_type_aliases(t, cls) for t in arg_t]

        log.debug(f"Converted: ({arg_t}) -> {res_t}")

        return arg_t, res_t

    def __set_name__(self, owner, name):
        if self.attrname is None:
            self.attrname = name
        elif name != self.attrname:
            raise TypeError(
                "Cannot assign the same bind to two different names "
                f"({self.attrname!r} and {name!r})."
            )

    # noinspection PyMethodOverriding
    def __get__(self, instance: object | None, owner_cls: Type[_CT]) -> _F:
        if self.attrname is None:
            raise TypeError(
                "Cannot use bind instance without calling __set_name__ on it."
            )

        if not self.func_set:
            argtypes, restype = self._get_defining_type_hints(owner_cls)
            self.py_api.restype = restype
            self.py_api.argtypes = argtypes
            self.func_set = True

        if instance is None:
            return self.py_api  # type: ignore

        try:
            cache = instance.__dict__
        except AttributeError:
            raise TypeError("bind requires classes to support __dict__.") from None

        bound_func = MethodType(self.py_api, instance)

        try:
            cache[self.attrname] = bound_func
        except TypeError:
            msg = (
                f"The '__dict__' attribute on {type(instance).__name__!r} instance "
                f"does not support item assignment for caching {self.attrname!r} property."
            )
            raise TypeError(msg) from None

        return bound_func
