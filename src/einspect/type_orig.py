"""Proxy for retrieving original methods and slot wrappers of types."""
from __future__ import annotations

from typing import Any, Type, TypeVar

_T = TypeVar("_T")
MISSING = object()

obj_getattr = object.__getattribute__
type_hash = type.__hash__
str_eq = str.__eq__
dict_setdefault = dict.setdefault
dict_contains = dict.__contains__
dict_get = dict.get
dict_getitem = dict.__getitem__

_slots_cache: dict[type, dict[str, Any]] = {}


def add_cache(type_: type, name: str, method: Any):
    """Add a method to the cache."""
    type_methods = dict_setdefault(_slots_cache, type_, {})
    # Only allow adding once, ignore if already added
    dict_setdefault(type_methods, name, method)


def in_cache(type_: type, name: str) -> bool:
    """Return True if the method is in the cache."""
    type_methods = dict_setdefault(_slots_cache, type_, {})
    return dict_contains(type_methods, name)


def get_cache(type_: type, name: str) -> Any:
    """Get the method from the type in cache."""
    type_methods = dict_setdefault(_slots_cache, type_, {})
    return dict_getitem(type_methods, name)


class orig:
    """
    Proxy to access a type's original attributes.

    Attributes on this object will mirror original attributes
    on the type before modification by @impl or TypeView.
    """

    def __new__(cls, type_: Type[_T]) -> Type[_T]:
        obj = object.__new__(cls)
        obj.__type = type_
        return obj  # type: ignore

    def __repr__(self) -> str:
        return f"orig({self.__type.__name__})"

    def __call__(self, *args, **kwargs):
        """Call the original type."""
        return self.__type(*args, **kwargs)

    def __getattribute__(self, name: str):
        """Get an attribute from the original type."""
        # Overrides
        _type = obj_getattr(self, "_orig__type")
        if str_eq(name, "_orig__type"):
            return _type

        # Check if the attribute is cached
        try:
            return get_cache(_type, name)
        except KeyError:
            pass
        # Get the attribute from the original type and cache it
        attr = getattr(_type, name)
        add_cache(_type, name, attr)
        return attr
