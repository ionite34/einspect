"""Decorator protocols for binding class properties."""
from __future__ import annotations

import ctypes
import inspect
import logging
from collections.abc import Callable
from functools import partial
from inspect import signature
from types import MethodType
from typing import TypeVar, get_type_hints

from einspect.protocols.type_parse import (
    FuncPtr,
    convert_type_hints,
    fix_ctypes_generics,
)

log = logging.getLogger(__name__)

_F = TypeVar("_F")
_R = TypeVar("_R")
_CT = TypeVar("_CT", bound=ctypes.Structure)


def bind_api(py_api: FuncPtr) -> Callable[[_F], _F]:
    """
    Decorator to bind a ctypes FuncPtr function to a class.

    Type hints of the decorated function are used to determine the
    argtypes and restype of the FuncPtr.
    """
    return partial(delayed_bind, py_api)


# noinspection PyPep8Naming
class delayed_bind(property):
    def __init__(self, py_api: FuncPtr, func: _F):
        super().__init__()
        # Use __func__ if staticmethod
        if isinstance(func, staticmethod):
            func = func.__func__
        self.func = func
        self.__doc__ = func.__doc__
        self.py_api = py_api
        self.attrname: str | None = None
        self.restype = None
        self.argtypes = None
        self.func_set = False

    def __repr__(self):
        return f"<{self.__class__.__name__} property {self.attrname!r}>"

    def __set_name__(self, owner: type, name: str) -> None:
        if self.attrname is None:
            self.attrname = name
        elif name != self.attrname:  # pragma: no cover
            raise TypeError(
                "Cannot assign the same bind to two different names "
                f"({self.attrname!r} and {name!r})."
            )

    def _get_defining_type_hints(self, owner_cls: type) -> tuple[list[type], type]:
        """Return the type hints for the attribute we're bound to, or None if it's not defined."""
        fix_ctypes_generics(self.func.__annotations__)
        # Get the function type hints
        hints = get_type_hints(self.func)
        log.debug(
            "[%s.%s()] Type hints: %s",
            owner_cls.__qualname__,
            self.attrname,
            hints,
        )
        res_t = hints.pop("return", None)
        arg_t = list(hints.values())

        # Disallow any missing type hints
        if None in arg_t or res_t is None:
            raise TypeError(
                "Cannot resolve bind function type hints. "
                "Please provide them explicitly."
            )

        res_t = convert_type_hints(res_t, owner_cls)

        # Insert current class type as first argument
        # If there is a "self" parameter
        if signature(self.func).parameters.get("self") and "self" not in hints:
            # Here we want to insert the actual class the function is defined
            # Not subclasses (in case a subclass gets the first call)
            def_cls = _get_defining_class_of_bound_method(self.func, owner_cls)
            log.debug("Found defining class: %s of %s", def_cls, self.func)
            arg_t.insert(0, def_cls)

        arg_t = [convert_type_hints(t, owner_cls) for t in arg_t]

        return arg_t, res_t

    # noinspection PyMethodOverriding
    def __get__(self, instance: object | None, owner_cls: type[_CT]) -> _F:
        if self.attrname is None:
            raise TypeError(
                "Cannot use bind instance without calling __set_name__ on it."
            )

        if not self.func_set:
            argtypes, restype = self._get_defining_type_hints(owner_cls)
            self.py_api.argtypes = argtypes
            self.py_api.restype = restype
            self.func_set = True
            if log.isEnabledFor(logging.DEBUG):
                log.debug(
                    "[%s.%s()] Set func: (%s) -> %r",
                    owner_cls.__name__,
                    self.attrname,
                    ", ".join(
                        repr(x.__name__) if x is not None else "None" for x in argtypes
                    ),
                    self.py_api.restype.__name__
                    if self.py_api.restype is not None
                    else "None",
                )

        # Called as class method, return directly without binding
        if instance is None:
            return self.py_api  # type: ignore

        try:
            cache = instance.__dict__
        except AttributeError:
            raise TypeError(
                "delayed_bind requires class to support __dict__."
            ) from None

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


def _get_defining_class_of_bound_method(method, current_cls) -> type:
    """Get defining class of a bound method."""
    for cls in inspect.getmro(current_cls):
        if method.__name__ in cls.__dict__:
            return cls
    raise ValueError(f"Failed to find defining class of {method!r}")
