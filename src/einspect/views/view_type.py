from __future__ import annotations

import sys
import weakref
from collections.abc import Generator, Sequence
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Callable, Literal, Type, TypeVar, Union, get_args

from typing_extensions import Self

from einspect._typing import is_union
from einspect.compat import Version
from einspect.errors import UnsafeError
from einspect.structs import PyDictObject, PyObject, PyTypeObject, TpFlags
from einspect.structs.slots_map import (
    Slot,
    get_slot,
    tp_as_async,
    tp_as_mapping,
    tp_as_number,
    tp_as_sequence,
)
from einspect.type_orig import (
    MISSING,
    add_impls,
    get_cache,
    get_impls,
    in_cache,
    in_impls,
    normalize_slot_attr,
    remove_impls,
    try_cache_attr,
)
from einspect.views.view_base import REF_DEFAULT, VarView

if TYPE_CHECKING:
    if sys.version_info >= (3, 9):
        from types import UnionType
    else:
        UnionType = type(Union)

__all__ = ("TypeView", "impl")

_T = TypeVar("_T")
_Fn = TypeVar("_Fn", bound=Callable)

AllocMode = Literal["mapping", "sequence", "all"]
ALLOC_MODES = frozenset({"mapping", "sequence", "all"})
PY_METHOD_STRUCTS = weakref.WeakKeyDictionary()


def get_func_name(func: Callable) -> str:
    """Returns the name of a method, class/static method, or property.."""
    return get_func_base(func).__name__


def get_func_base(func: Callable) -> Callable:
    """Returns the base function of a method, class/static method, or property."""
    if isinstance(func, property):
        return func.fget
    elif isinstance(func, (classmethod, staticmethod)):
        return func.__func__
    return func


def _to_types(
    types_or_unions: Sequence[type | UnionType],
) -> Generator[type, None, None]:
    """Yields types from a Sequence of types or unions."""
    for t in types_or_unions:
        if isinstance(t, type):
            yield t
        elif is_union(t):
            yield from _to_types(get_args(t))
        else:
            raise TypeError(f"cls must be a type or Union, not {t.__class__.__name__}")


def _restore_impl(*types: type, name: str) -> None:
    """
    Finalizer to restore the original `name` attribute on type(s).

    If there is no original attribute, delete the attribute.
    """
    for t in types:
        v = TypeView(t, ref=False)
        # Get the original attribute from cache
        if in_cache(t, name):
            attr = get_cache(t, name)
            if attr is not MISSING:
                # Set the attribute back using a view
                v[name] = normalize_slot_attr(attr)

        # No original attribute, delete the attribute
        with v.as_mutable():
            del v[name]


def _attach_finalizer(types: Sequence[type], func: Callable) -> None:
    """Attaches a finalizer to the function to remove the implemented method on types."""
    # Use the base function (we can't set attributes on properties)
    func = get_func_base(func)
    name = func.__name__
    # Don't finalize types that are already registered
    if hasattr(func, "_impl_types"):
        types = [t for t in types if t not in func._impl_types]
        # Update list
        func._impl_types.extend(types)
    else:
        func._impl_types = list(types)

    func._impl_finalize = weakref.finalize(func, _restore_impl, *types, name=name)


def _patch_object_base() -> None:
    """
    Adds a new PyTypeObject into base mro of `object`.

    This allows for PyMethods allocations on `object` without
    breaking CPython's assumption checks on `object` having
    PyMethod pointers as NULL.

    Reference logic for object patch by chilaxan in:
      - https://github.com/chilaxan/fishhook/blob/master/fishhook/fishhook.py
    """
    obj = PyTypeObject.from_object(object)

    # Skip if already patched
    if obj.tp_base:
        return

    base = PyTypeObject(
        ob_refcnt=1,
        ob_type=PyTypeObject.from_object(type).as_ref(),
        tp_name=b"base_object",
        tp_basicsize=object.__basicsize__,
        tp_flags=TpFlags.READY | TpFlags.IMMUTABLETYPE,
        tp_dict=PyObject.from_object({}).with_ref().as_ref(),
        tp_bases=PyObject.from_object(()).with_ref().as_ref(),
    )

    # Keep a reference to the base object
    PY_METHOD_STRUCTS.setdefault(object, []).append(base)

    # Patch to object
    obj.tp_base = base.as_ref()

    # Since some internal code paths find `object` by expecting `__base__` to be None,
    # we need to patch `type.__base__` to return None on `object`.
    orig_base = vars(type)["__base__"].__get__
    _object = object

    @property
    def __base__(self):
        if self is _object:
            return None
        return orig_base(self)

    type_obj = PyTypeObject.from_object(type)
    type_obj.tp_dict.contents.astype(PyDictObject).SetItem("__base__", __base__)
    type_obj.Modified()


def _allocate_methods(obj: PyTypeObject, *slots: Slot, subclasses: bool = True) -> None:
    """
    Allocate PyMethods structs on the type.

    Args:
        obj: The type to allocate the PyMethod struct on.
        slots: The slots to allocate.
        subclasses: If True, will allocate the PyMethod struct on subclasses as well.
    """
    # Skip if no slots or no PyMethods struct on any slot
    if not slots or not any(slot.ptr_type for slot in slots):
        return

    # For object, need to run a patch for bases
    if obj == object:
        _patch_object_base()

    py_obj = obj.into_object()

    if obj.ob_type.contents != type:
        raise TypeError(
            f"During allocation for {obj.into_object()}: obj must be a type, not {obj.ob_type[0].into_object()!r}"
        )

    if subclasses and obj != type:
        sub_fn = obj.ob_type.contents.GetAttr("__subclasses__")
        for t in sub_fn(py_obj):
            py_type = PyTypeObject.from_object(t)
            if py_type.ob_type.contents != type:
                continue
            _allocate_methods(PyTypeObject.from_object(t), *slots)

    for slot in slots:
        # Skip if no PyMethods struct for slot
        if not slot.ptr_type:
            continue
        # Allocate if the slot is null
        if not (py_method := getattr(obj, slot.parts[0])):
            new_struct = slot.ptr_type()
            # Need to keep a reference to the PyMethod struct,
            # so it doesn't get garbage collected.
            # Here we append it to a WeakKeyDictionary
            PY_METHOD_STRUCTS.setdefault(py_obj, []).append(new_struct)
            py_method.contents = new_struct


def impl(
    *cls: Type[_T] | type | UnionType,
    alloc: AllocMode | None = None,
    detach: bool = False,
) -> Callable[[_Fn], _Fn]:
    # noinspection PyShadowingNames, PyCallingNonCallable
    """
    Decorator for implementing methods on types.

    Supports methods decorated with property, classmethod, or staticmethod.

    Args:
        cls: The type(s) or Union(s) to implement the method on.
        alloc: The PyMethod allocation mode. Default of None will automatically allocate
            PyMethod structs as needed. If "sequence" or "mapping", will prefer the
            respective PySequenceMethods or PyMappingMethods in cases of ambiguious slot names.
            (e.g. "__getitem__" or "__len__"). If "all", will allocate all PyMethod structs.
        detach: If True, will remove the implemented method from the type when
            the decorated function is garbage collected. This will hold a reference to
            the type(s) for the lifetime of the function. Requires function to support weakrefs.

    Returns:
        The original function after it has been implemented on the types,
        allows chaining of multiple impl decorators.

    Examples:
        >>> @impl(int)
        ... def is_even(self):
        ...     return self % 2 == 0

        >>> @impl(int | float)  # or @impl(int, float)
        ... @classmethod
        ... def try_from(cls, value):
        ...     try:
        ...         return cls(value)
        ...     except ValueError:
        ...         return None
    """
    targets = tuple(_to_types(cls))

    def wrapper(func: _Fn) -> _Fn:
        # detach requires weakrefs
        if detach:
            try:
                weakref.ref(get_func_base(func))
            except TypeError:
                raise TypeError(
                    f"detach=True requires function {func!r} to support weakrefs"
                ) from None

        name = get_func_name(func)

        for type_ in targets:
            t_view = TypeView(type_)
            with t_view.alloc_mode(alloc):
                t_view[name] = func

        if detach:
            _attach_finalizer(targets, func)

        return func

    return wrapper


class TypeView(VarView[_T, None, None]):
    _pyobject: PyTypeObject[_T]

    def __init__(self, obj: _T, ref: bool = REF_DEFAULT) -> None:
        """Create a new TypeView."""
        super().__init__(obj, ref)
        self._alloc_mode = None

    @property
    def immutable(self) -> bool:
        """Return True if the type is immutable."""
        if Version.PY_3_10.above():
            return bool(self._pyobject.tp_flags & TpFlags.IMMUTABLETYPE)
        return not bool(self._pyobject.tp_flags & TpFlags.HEAPTYPE)  # pragma: no cover

    @immutable.setter
    def immutable(self, value: bool):
        """Set whether the type is immutable."""
        if Version.PY_3_10.above():
            if value:
                self._pyobject.tp_flags |= TpFlags.IMMUTABLETYPE
            else:
                self._pyobject.tp_flags &= ~TpFlags.IMMUTABLETYPE
        else:  # pragma: no cover
            if value:
                self._pyobject.tp_flags &= ~TpFlags.HEAPTYPE
            else:
                self._pyobject.tp_flags |= TpFlags.HEAPTYPE

    @contextmanager
    def as_mutable(self) -> Generator[Self, None, None]:
        """Context manager to temporarily set the type as mutable."""
        if not self.immutable:
            yield self
            return
        self.immutable = False
        self._pyobject.Modified()
        yield self
        self.immutable = True
        self._pyobject.Modified()

    @contextmanager
    def alloc_mode(self, mode: AllocMode | None):
        """Context manager to temporarily set the type's allocation mode."""
        if mode is None:
            yield self
            return
        mode = mode.casefold() if mode else None
        if mode is not None and mode not in ALLOC_MODES:
            raise ValueError(
                f"Invalid alloc mode: {mode!r}, must be 'mapping', 'sequence', or 'all'"
            )
        orig = self._alloc_mode
        self._alloc_mode = mode
        yield self
        self._alloc_mode = orig

    def alloc_slot(self, *slot: Slot, subclasses: bool = True) -> None:
        """
        Allocate slot method structs. Defaults to all the following:

        - tp_as_async (PyAsyncMethods)
        - tp_as_number (PyNumberMethods)
        - tp_as_mapping (PyMappingMethods)
        - tp_as_sequence (PySequenceMethods)
        """
        slots = slot or (tp_as_async, tp_as_number, tp_as_mapping, tp_as_sequence)
        _allocate_methods(self._pyobject, *slots, subclasses=subclasses)

    def restore(self, *names: str | Callable) -> None:
        """
        Restore named attribute(s) on type.

        Args:
            *names: Optional name(s) of attribute(s) to restore.
                Can be str or callable with ``__name__``. If empty, restore all attributes.
        """
        type_ = self._pyobject.into_object()

        if not names:
            # Restore all attributes
            names = get_impls(type_)

        # Normalize names of stuff like properties and class methods
        names = [get_func_name(n) if callable(n) else n for n in names]
        # Check all names exist first
        for name in names:
            if in_impls(type_, name) and in_cache(type_, name):
                attr = get_cache(type_, name)
                # MISSING is a special case, it means there is no original attribute
                if attr is MISSING:
                    # Same as no attribute, delete it
                    del self[name]
                    remove_impls(type_, name)
                else:
                    self[name] = normalize_slot_attr(attr)
            # If in impl record, and not in cache, remove the attribute
            elif in_impls(type_, name):
                del self[name]
                remove_impls(type_, name)
            else:
                raise AttributeError(
                    f"{type_.__name__!r} has no original attribute {name!r}"
                )

    def __getitem__(self, name: str) -> Any:
        """Get an attribute from the type object."""
        return self._pyobject.GetAttr(name)

    def __setitem__(self, names: str | tuple[str, ...], value: Any) -> None:
        """
        Set attributes on the type object.

        Multiple string keys can be used to set multiple attributes to the same value.
        """
        keys = (names,) if isinstance(names, str) else names
        # For all alloc mode, allocate now
        if self._alloc_mode == "all":
            self.alloc_slot()
        for name in keys:
            base = self.base
            # Add impls record
            add_impls(base, name)
            # Cache original implementation
            try_cache_attr(base, name)
            # Check if this is a slots attr (skip all since we already allocated)
            if self._alloc_mode != "all" and (
                slot := get_slot(name, prefer=self._alloc_mode)
            ):
                # Allocate sub-struct if needed
                self.alloc_slot(slot)

            with self.as_mutable():
                self._pyobject.setattr_safe(name, value)

    def __delitem__(self, names: str | tuple[str, ...]) -> None:
        """Delete attributes from the type object."""
        keys = (names,) if isinstance(names, str) else names
        for name in keys:
            base = self.base
            # Add impls record
            add_impls(base, name)
            # Cache original implementation
            try_cache_attr(base, name)

            with self.as_mutable():
                self._pyobject.delattr_safe(name)

    def __getattr__(self, item: str):
        # Forward `tp_` attributes from PyTypeObject
        if item.startswith("tp_"):
            return getattr(self._pyobject, item)
        raise AttributeError(item)

    def __setattr__(self, key: str, value: Any) -> None:
        if key in type(self).__dict__:
            return super().__setattr__(key, value)
        # Forward `tp_` attributes from PyTypeObject
        if key.startswith("tp_") and hasattr(self._pyobject, key):
            if not self._unsafe:
                raise UnsafeError(
                    f"Setting attribute {key} requires an unsafe context."
                )
            setattr(self._pyobject, key, value)
            return
        super().__setattr__(key, value)

    @property
    def tp_name(self) -> str:
        """Return the type's name."""
        return self._pyobject.tp_name.decode("utf-8")

    @tp_name.setter
    def tp_name(self, value: str) -> None:
        """Set the type's name."""
        self._pyobject.tp_name = value.encode("utf-8")

    @property
    def tp_flags(self) -> TpFlags:
        """Return the type's flags."""
        return TpFlags(self._pyobject.tp_flags)

    @tp_flags.setter
    def tp_flags(self, value: int | TpFlags) -> None:
        """Set the type's flags."""
        self._pyobject.tp_flags = value
