"""Proxy for retrieving original methods and slot wrappers of types."""
from __future__ import annotations

from ctypes import cast
from types import BuiltinFunctionType
from typing import Any, Type, TypeVar
from weakref import WeakKeyDictionary

from einspect.structs.include.object_h import newfunc
from einspect.structs.py_type import PyTypeObject, TypeNewWrapper

_T = TypeVar("_T")

# Singleton to cache for attributes that don't exist on the type
MISSING = object()

# Statically cache some methods used in cache lookups
obj_tp_new = cast(PyTypeObject.from_object(object).tp_new, newfunc)
obj_getattr = object.__getattribute__
type_hash = type.__hash__
str_eq = str.__eq__

dict_setdefault = dict.setdefault
dict_setitem = dict.__setitem__
dict_contains = dict.__contains__
dict_getitem = dict.__getitem__
dict_get = dict.get

set_contains = set.__contains__

wk_dict_setdefault = WeakKeyDictionary.setdefault
wk_dict_getitem = WeakKeyDictionary.__getitem__
wk_dict_get = WeakKeyDictionary.get

# Cache of original type attributes, keys are weakrefs to not delay GC of user types
_cache: WeakKeyDictionary[type, dict[str, Any]] = WeakKeyDictionary()
_impls: WeakKeyDictionary[type, set[str]] = WeakKeyDictionary()


def add_cache(type_: type, name: str, method: Any, overwrite: bool = False) -> Any:
    """Add a type's attribute to the cache."""
    type_attrs = wk_dict_setdefault(_cache, type_, {})

    # For `__new__` methods, use special TypeNewWrapper for modified safety check
    if name == "__new__":
        # Check if we're trying to set a previous impl method
        # If so, avoid the loop by using object.__new__
        if not isinstance(method, BuiltinFunctionType):
            method = get_cache(object, "__new__")
        else:
            tp_new = PyTypeObject.from_object(type_).tp_new
            method = obj_tp_new(TypeNewWrapper, (), {})
            method.__init__(tp_new, type_)

    if overwrite:
        dict_setitem(type_attrs, name, method)
    else:
        dict_setdefault(type_attrs, name, method)

    return method


def add_impls(type_: type, *attrs: str) -> None:
    """Add a set of implemented attributes to the cache."""
    attrs_set = wk_dict_setdefault(_impls, type_, set())
    attrs_set.update(attrs)


def remove_impls(type_: type, *attrs: str) -> None:
    """Remove a set of implemented attributes from the cache."""
    attrs_set = wk_dict_getitem(_impls, type_)
    if attrs_set is not None:
        for attr in attrs:
            attrs_set.discard(attr)


def try_cache_attr(
    type_: type,
    name: str,
    flag_missing: bool = True,
    exists_ok: bool = True,
    overwrite: bool = False,
) -> None:
    """
    Caches a type's attribute if it exists.

    Args:
        type_: The type to cache the attribute for.
        name: The name of the attribute.
        flag_missing: If True, add the `type_orig.MISSING` object to cache if it doesn't exist.
        exists_ok: If False, raise KeyError if the attribute is already in cache.
        overwrite: If True, overwrite the attribute in cache if it already exists.
    """
    # Check if the attribute is already in cache
    if not exists_ok and in_cache(type_, name):
        raise ValueError(f"Attribute {name!r} is already in cache for type {type_!r}")

    # Get the attribute
    try:
        attr = getattr(type_, name)
    except AttributeError:
        if flag_missing:
            attr = MISSING
        else:
            return

    # Add the attribute to the cache
    add_cache(type_, name, attr, overwrite=overwrite)


def in_cache(type_: type, name: str) -> bool:
    """Return True if the method is in the cache."""
    type_methods = wk_dict_setdefault(_cache, type_, {})
    return dict_contains(type_methods, name)


def in_impls(type_: type, name: str) -> bool:
    """Return True if the attribute is in the impls cache."""
    attrs_set = wk_dict_get(_impls, type_)
    return set_contains(attrs_set, name) if attrs_set else False


def get_cache(type_: type, name: str) -> Any:
    """Get the method from the type in cache."""
    type_methods = wk_dict_setdefault(_cache, type_, {})
    try:
        return dict_getitem(type_methods, name)
    except KeyError:
        raise KeyError(
            f"Original attribute {name!r} was not found for type {type_!r}"
        ) from None


def get_type_cache(type_: type) -> dict[str, Any]:
    """Get the cache for the type."""
    try:
        return wk_dict_getitem(_cache, type_)
    except KeyError:
        raise KeyError(
            f"Original attributes cache was not found for type {type_!r}"
        ) from None


def get_impls(type_: type) -> set[str]:
    """Get the impls cache for the type."""
    try:
        return wk_dict_getitem(_impls, type_)
    except KeyError:
        raise KeyError(
            f"Original attributes cache was not found for type {type_!r}"
        ) from None


def normalize_slot_attr(attr: object | TypeNewWrapper) -> Any:
    """Normalize a slot attribute to its original value."""
    if isinstance(attr, TypeNewWrapper):
        return attr._orig_slot_fn
    return attr


add_cache(object, "__new__", object.__new__)
add_cache(type, "__new__", type.__new__)


class orig:
    """
    Proxy to access a type's original attributes.

    Attributes on this object will mirror original attributes
    on the type before modification by @impl or TypeView.
    """

    def __new__(cls, type_: Type[_T]) -> Type[_T]:
        # To avoid a circular call loop when orig is called within
        # impl of object.__new__, we use the raw tp_new of object here.
        self = obj_tp_new(cls, (), {})
        self.__type = type_
        return self  # type: ignore

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
        return add_cache(_type, name, attr)
