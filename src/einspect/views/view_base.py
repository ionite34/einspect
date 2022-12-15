from __future__ import annotations

import ctypes
import logging
import warnings

import weakref
from abc import ABC
from contextlib import contextmanager, ExitStack
from copy import deepcopy
from ctypes import py_object
from typing import Generic, get_type_hints, TypeVar, ContextManager

from typing_extensions import Final, Self

from einspect.views import factory
from einspect.api import Py, PyObj_FromPtr
from einspect.errors import UnsafeError, MovedError, UnsafeAttributeError
from einspect.structs import PyObject, PyVarObject
from einspect.views.unsafe import unsafe, Context

log = logging.getLogger(__name__)

_T = TypeVar("_T")

NO_REF = object()
REF_DEFAULT: Final[bool] = True


class BaseView(ABC, Generic[_T]):
    def __init__(self, obj: _T, ref: bool = REF_DEFAULT) -> None:
        # Attempt to get a weakref if possible
        try:
            self._base_weakref = weakref.ref(obj)
        except TypeError:
            self._base_weakref = None

        # Stores base info for repr and errors
        self._base_type = type(obj)
        self._base_id = id(obj)

        self._local_unsafe = False

        # Strong reference
        self._base = NO_REF
        if ref:
            # Convert to py_object
            if not isinstance(obj, py_object):
                obj = py_object(obj)
            self._base = obj

    @property
    def _unsafe(self) -> bool:
        """Check if either _local_unsafe or _global_unsafe is set."""
        if self._local_unsafe:
            return True
        # noinspection PyProtectedMember
        return Context._global_unsafe

    @contextmanager
    def unsafe(self) -> ContextManager[Self]:
        """Context manager to allow unsafe attribute edits."""
        self._local_unsafe = True
        yield self
        self._local_unsafe = False


class View(BaseView[_T]):
    """
    View for Python objects.

    Notes:
        The _pyobject class annotation is used to determine
        the type of the underlying PyObject struct.
    """
    _pyobject: PyObject

    def __init__(self, obj: _T, ref: bool = REF_DEFAULT) -> None:
        super().__init__(obj, ref)
        struct_type = get_type_hints(self.__class__)["_pyobject"]
        self._pyobject = struct_type.from_object(obj)

    def __repr__(self) -> str:
        addr = self._pyobject.address
        py_obj_cls = self._pyobject.__class__.__name__
        return f"{self.__class__.__name__}[{self._base_type.__name__}](<{py_obj_cls} at 0x{addr:x}>)"

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
        if self._base is not NO_REF:
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
                        RuntimeWarning
                    )

        return self._pyobject.into_object()

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
    def type(self) -> type:
        """Type of the object."""
        return self._pyobject.ob_type

    @type.setter
    def type(self, value: type) -> None:
        if not self._unsafe:
            raise UnsafeAttributeError.from_attr("type")
        self._pyobject.ob_type = value

    @property
    def mem_size(self) -> int:
        """
        Memory size of the object in bytes.

        Notes:
            This will require casting into a py_object to use __sizeof__.
            If (ref=False), and the object does not support weakrefs,
            accessing this attribute will require an unsafe context.
        """
        return self.base.__sizeof__()

    @unsafe
    def move_to(self, dst) -> None:
        """Copy the object to another view's location."""
        if not isinstance(dst, View):
            raise TypeError(f"Expected View, got {type(dst).__name__!r}")
        ctypes.memmove(
            dst._pyobject.address,
            self._pyobject.address,
            self.mem_size
        )

    @unsafe
    def move_from(self, other) -> Self:
        """Moves data at other to this view."""
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
        return v

    def __ilshift__(self, other):
        """Moves data at other to this view."""
        return self.move_from(other)

    def __invert__(self) -> py_object[_T]:
        """Returns the base of this view as py_object."""
        # Prioritize strong ref if it exists
        if self._base is not NO_REF:
            return self._base
        return self.base


class VarView(View[_T]):
    _pyobject: PyVarObject

    @property
    def size(self) -> int:
        """Size of the list."""
        return int(self._pyobject.ob_size)  # type: ignore

    @size.setter
    def size(self, value: int) -> None:
        if not self._unsafe:
            raise UnsafeAttributeError.from_attr("size")
        self._pyobject.ob_size = value
