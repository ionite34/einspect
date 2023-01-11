from __future__ import annotations

import ctypes
import logging
import warnings
import weakref
from abc import ABC
from contextlib import ExitStack
from copy import deepcopy
from ctypes import py_object, sizeof
from typing import Final, Generic, Type, TypeVar, get_type_hints

from einspect.api import Py, PyObj_FromPtr
from einspect.errors import (
    DroppedReference,
    MovedError,
    UnsafeAttributeError,
    UnsafeError,
)
from einspect.structs import PyObject, PyVarObject
from einspect.views._display import format_display
from einspect.views.unsafe import UnsafeContext, unsafe

__all__ = ("View", "VarView", "AnyView", "REF_DEFAULT")

log = logging.getLogger(__name__)

REF_DEFAULT: Final[bool] = True

_T = TypeVar("_T")
_KT = TypeVar("_KT")
_VT = TypeVar("_VT")
_V = TypeVar("_V", bound="View")


def _wrap_py_object(obj: _T | py_object[_T]) -> py_object[_T]:
    """Wrap non-py_object objects in a py_object."""
    if isinstance(obj, py_object):
        return obj
    return py_object(obj)


class BaseView(ABC, Generic[_T, _KT, _VT], UnsafeContext):
    """Base class for all views."""

    def __init__(self, obj: _T, ref: bool = REF_DEFAULT) -> None:
        super().__init__()
        # Stores base info for repr and errors
        self._base_type: type[_T] = type(obj)
        self._base_id = id(obj)
        # Get a reference if ref=True
        self._base: py_object[_T] | None = _wrap_py_object(obj) if ref else None
        # Attempt to get a weakref
        try:
            self._base_weakref = weakref.ref(obj)
        except TypeError:
            self._base_weakref = None


class View(BaseView[_T, _KT, _VT]):
    """
    View for Python objects.

    Notes:
        The _pyobject class annotation is used to determine
        the type of the underlying PyObject struct.
    """

    _pyobject: PyObject[_T, None, None]

    def __init__(self, obj: _T, ref: bool = REF_DEFAULT) -> None:
        super().__init__(obj, ref)
        struct_type = get_type_hints(self.__class__)["_pyobject"]
        self._pyobject = struct_type.from_object(obj)
        self.__dropped = False

    def __repr__(self) -> str:
        addr = self._pyobject.address
        py_obj_cls = self._pyobject.__class__.__name__
        return f"{self.__class__.__name__}(<{py_obj_cls} at 0x{addr:x}>)"

    def info(self, types: bool = True) -> str:
        """Returns info about the view."""
        return format_display(self, types=types)

    @property
    def ref_count(self) -> int:
        """Reference count of the object."""
        return int(self._pyobject.ob_refcnt)  # type: ignore

    @ref_count.setter
    def ref_count(self, value: int) -> None:
        if not self._unsafe:
            raise UnsafeAttributeError.from_attr("ref_count")
        self._pyobject.ob_refcnt = value

    @property
    def type(self) -> Type[_T]:
        """Type of the object."""
        return self._pyobject.ob_type.contents.into_object().value  # type: ignore

    @type.setter
    def type(self, value: type) -> None:
        if not self._unsafe:
            raise UnsafeAttributeError.from_attr("type")
        self._pyobject.ob_type = value

    @property
    def base(self) -> py_object[_T]:
        """
        Returns the base object of the view.

        Requires either the View to be created with (ref=True)
        or the object to support weakrefs.

        Notes:
            If neither ref nor weakref are available, and called within an
            unsafe context, returns an object via memory address cast.
            The result of the cast is undefined behavior, and could cause
            a segmentation fault.

        Returns:
            The base object of the view.

        Raises:
            AttributeError: If ref=False and base does not support weakrefs.
            MovedError: If weak-ref of base is garbage collected.
        """
        # Prioritize strong ref if it exists
        if self._base is not None:
            return self._base
        # If no weakref, error if no unsafe context
        if self._base_weakref is None:
            if not self._unsafe:
                raise UnsafeError(
                    f"Base object {self._base_type.__name__!r} does not support weak-refs, "
                    "use (ref=True) or an unsafe context to access base via memory address."
                ) from None
            else:
                # Give a resource warning if ref_count is <= 0
                ref_count = self.ref_count
                if ref_count <= 0:
                    warnings.warn(
                        f"Base object {self._base_type.__name__!r} has ref_count <= 0, "
                        "Accessing base via memory address is undefined behavior.",
                        RuntimeWarning,
                    )
        # Attempt to use weakref if alive
        else:
            base = self._base_weakref()
            if base is not None:
                return py_object(base)
            else:
                if not self._unsafe:
                    raise MovedError(
                        f"Weak-referenced base object {self._base_type.__name__!r} has been garbage collected. "
                        "use unsafe context to access base via memory address."
                    ) from None
                else:
                    # Resource warning
                    warnings.warn(
                        f"Weak-referenced base object {self._base_type.__name__!r} has been garbage collected. "
                        "Accessing base via memory address is undefined behavior.",
                        RuntimeWarning,
                    )

        return self._pyobject.into_object()

    @property
    def mem_size(self) -> int:
        """Memory size of the object in bytes."""
        return sizeof(self._pyobject)

    def drop(self) -> None:
        """
        Drop all references to the base object.

        Notes:
            This is useful for when you want to drop the reference
            to the base object, but still want to access the view.
        """
        ref = DroppedReference(type(self))
        self._pyobject = ref  # type: ignore
        self._base = ref  # type: ignore
        self._base_weakref = None
        self.__dropped = True

    @unsafe
    def move_to(self, dst: View, start: int = 8) -> None:
        """
        Copy the object to another view's location.

        Args:
            dst: The destination view.
            start: The start offset in bytes to copy from.
                The default of 8 is to skip `ob_refcnt`
        """
        if not isinstance(dst, View):
            raise TypeError(f"Expected View, got {type(dst).__name__!r}")
        ctypes.memmove(
            dst._pyobject.address + start,
            self._pyobject.address + start,
            self.mem_size - start,
        )

    @unsafe
    def move_from(self, other: _V) -> _V:
        """Moves data at other View to this View."""
        from einspect.views import factory

        # Store our repr
        self_repr = repr(self)
        # Store our current address
        addr = self._pyobject.address
        if not isinstance(other, View):
            with ExitStack() as stack:
                # Add a temp ref to prevent GC before we're done moving
                Py.IncRef(other)
                stack.callback(Py.DecRef, other)
                # Take a deepcopy to prevent issues with members being GC'd
                other = deepcopy(other)
                # Prevent new deepcopy being dropped by adding a reference
                Py.IncRef(other)
                other = factory.view(other)

        # Move other to our pyobject address
        with other.unsafe():
            other.move_to(self)
        # Return a new view of ourselves
        obj = PyObj_FromPtr(addr)
        # Increment ref count before returning
        Py.IncRef(obj)
        v = factory.view(obj)
        log.debug(f"Moved {other} to {self_repr} -> {v}")
        log.debug(f"New ref count: {v.ref_count}")
        # Drop the current view
        self.drop()
        return v

    def __lshift__(self, other: _V) -> _V:
        """Moves data at other View to this View."""
        return self.move_from(other)

    def __invert__(self) -> _T:
        """Returns the base of this view as object."""
        # Prioritize strong ref if it exists
        if self._base is not None:
            return self._base.value
        return self.base.value


class VarView(View[_T, _KT, _VT]):
    _pyobject: PyVarObject[_T, _KT, _VT]

    @property
    def size(self) -> int:
        """Size (ob_size) of the PyVarObject."""
        return self._pyobject.ob_size

    @size.setter
    @unsafe
    def size(self, value: int) -> None:
        self._pyobject.ob_size = value


class AnyView(View[_T, None, None]):
    _pyobject: PyObject[_T, _KT, _VT]

    @property
    def mem_size(self) -> int:
        """
        Memory size of the object in bytes.

        Notes:
            This will require casting into a py_object to use __sizeof__.
            If (ref=False), and the object does not support weakrefs,
            accessing this attribute will require an unsafe context.
        """
        return object.__sizeof__(self.base.value)

    def __repr__(self) -> str:
        addr = self._pyobject.address
        py_obj_cls = self._pyobject.__class__.__name__
        return f"{self.__class__.__name__}[{self._base_type.__name__}](<{py_obj_cls} at 0x{addr:x}>)"
