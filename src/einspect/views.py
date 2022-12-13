"""Data views onto built-in objects."""
from __future__ import annotations

import ctypes
import warnings
import weakref
from abc import ABC
from collections.abc import Sequence, Iterable, Callable
from contextlib import contextmanager, ExitStack
from copy import deepcopy
from ctypes import pythonapi, py_object, Array
from functools import wraps
from typing import TypeVar, Generic, overload, get_type_hints

from typing_extensions import Self

from einspect.api import Py, PyObj_FromPtr
from einspect.errors import MovedError, UnsafeIndexError, UnsafeAttributeError, UnsafeError
from einspect.structs import PyObject, PyListObject, PyTupleObject, Py_ssize_t, PyLongObject, PyVarObject
from einspect.utils import new_ref

_IntType = TypeVar("_IntType", bound=int)
_ListType = TypeVar("_ListType", bound=list)
_TupleType = TypeVar("_TupleType", bound=tuple)
_T = TypeVar("_T")
_S = TypeVar("_S")

NO_REF = object()


@overload
def view(obj: _IntType, ref: bool = False) -> IntView[_IntType]: ...


@overload
def view(obj: _ListType, ref: bool = False) -> ListView[_ListType]:
    ...


@overload
def view(obj: _TupleType, ref: bool = False) -> TupleView[_ListType]:
    ...


@overload
def view(obj: _T, ref: bool = False) -> View[_T]:
    ...


def view(obj, ref: bool = True):
    """
    Create a view onto a Python object.

    Args:
        obj: The object to view.
        ref: If True, hold a strong reference to the object.

    Returns: A view onto the object.
    """
    if isinstance(obj, list):
        return ListView(obj, ref=ref)
    elif isinstance(obj, tuple):
        return TupleView(obj, ref=ref)
    elif isinstance(obj, int):
        return IntView(obj, ref=ref)
    else:
        # Base case
        return View(obj, ref=ref)


view.__getitem__ = lambda self, item: self.getitem(item)


# noinspection PyPep8Naming
class unsafe_property(property):
    """Property that requires self._unsafe to be True."""

    def unsafe_setter(self, func):
        """Set an unsafe setter for this property."""
        res = type(self)(self.fget, self.fset, self.fdel, self.__doc__)
        res.fset = func
        return res

    def __set__(self, obj: BaseView, value):
        """If _unsafe is True, use direct set, otherwise setter."""
        # noinspection PyProtectedMember
        if obj._unsafe:
            return self.fset_unsafe(obj, value)
        # If _unsafe is False and setter does not exist, raise AttributeError
        if self.fset is None:
            raise AttributeError("can't set attribute without unsafe context")
        super().__set__(obj, value)

    fset_unsafe = property.fset


def unsafe(func: Callable) -> Callable:
    """Decorator for unsafe methods on View subclasses."""

    @wraps(func)
    def wrapper(self: View, *args, **kwargs):
        # noinspection PyProtectedMember
        if not self._unsafe:
            raise UnsafeError(f"Call to {func.__name__} requires unsafe context")
        return func(self, *args, **kwargs)

    return wrapper


class BaseView(ABC, Generic[_T]):
    def __init__(self, obj: _T, ref: bool = True) -> None:
        # Attempt to get a weakref if possible
        try:
            self._base_weakref = weakref.ref(obj)
        except TypeError:
            self._base_weakref = None

        # Stores base info for repr and errors
        self._base_type = type(obj)
        self._base_id = id(obj)

        self._unsafe = False

        # Strong reference
        self._base = NO_REF
        if ref:
            # Convert to py_object
            if not isinstance(obj, py_object):
                obj = py_object(obj)
            self._base = obj

    @contextmanager
    def unsafe(self) -> Self:
        """Context manager to allow unsafe attribute edits."""
        self._unsafe = True
        yield self
        self._unsafe = False


class View(BaseView[_T]):
    """
    View for Python objects.

    Notes:
        The _pyobject class annotation is used to determine
        the type of the underlying PyObject struct.
    """
    _pyobject: PyObject

    def __init__(self, obj: _T, ref: bool = True) -> None:
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
                other = view(other)

        # Move other to our pyobject address
        with other.unsafe():
            other.move_to(self)
        # Return a new view of ourselves
        obj = PyObj_FromPtr(addr)
        return view(obj)

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


class ListView(VarView[_T], Sequence):
    _pyobject: PyListObject

    @overload
    def __getitem__(self, index: int):
        ...

    @overload
    def __getitem__(self, index: slice):
        ...

    def __getitem__(self, index: int):
        if isinstance(index, int):
            # First use PyList_GetItem
            try:
                ret = pythonapi.PyList_GetItem(self._pyobject, index)
                return ret
            except IndexError as err:
                raise IndexError(f"Index {index} out of range") from err
        elif isinstance(index, slice):
            raise NotImplementedError
        else:
            raise TypeError(f"Invalid index type: {type(index)}")

    def __setitem__(self, key: int, value: _S) -> None:
        # First use PyList_SetItem
        try:
            ref = new_ref(value)
            pythonapi.PyList_SetItem(self._pyobject, key, ref)
        except IndexError as err:
            if not self._unsafe:
                raise UnsafeAttributeError.from_attr("__setitem__") from err
            else:
                # If unsafe, use direct set
                self._pyobject.ob_item[key] = new_ref(value)

    def __len__(self) -> int:
        x = self.size
        if x > 5:
            return x
        return self.size

    @property
    def allocated(self) -> int:
        """Allocated size of the list."""
        return int(self._pyobject.allocated)  # type: ignore

    @allocated.setter
    def allocated(self, value: int) -> None:
        if not self._unsafe:
            raise UnsafeAttributeError.from_attr("allocated")
        self._pyobject.allocated = value

    @property
    def item(self) -> list:
        """List of items in the list."""
        return self._pyobject.ob_item

    @item.setter
    def item(self, value: list) -> None:
        if not self._unsafe:
            raise UnsafeAttributeError.from_attr("item")
        self._pyobject.ob_item = value


class TupleView(VarView[_T], Sequence):
    _pyobject: PyTupleObject
    
    @overload
    def __getitem__(self, index: int):
        ...

    @overload
    def __getitem__(self, index: slice):
        ...

    def __getitem__(self, index: int):
        if isinstance(index, int):
            # First use PyList_GetItem
            try:
                addr = self._pyobject.GetItem(self._pyobject, index)
                return addr
            except IndexError as err:
                raise IndexError(f"Index {index} out of range") from err
        elif isinstance(index, slice):
            raise NotImplementedError
        else:
            raise TypeError(f"Invalid index type: {type(index)}")

    def __setitem__(self, key: int, value: _S) -> None:
        # First use SetItem api
        try:
            # Get current item and decref
            prev_item = self._pyobject.GetItem(self._pyobject, key)
            # pythonapi.Py_DecRef(prev_item)
            # ref = ctypes.py_object(value)
            # pythonapi.Py_IncRef(ref)
            ref = new_ref(value)
            arr = self.item
            arr[key] = ref
            # self._pyobject.SetItem(self._pyobject, key, ref)
        except IndexError as err:
            if not self._unsafe:
                raise UnsafeIndexError(
                    "Setting indices beyond current size requires entering the unsafe() context."
                ) from err
            else:
                if key < 0:
                    raise IndexError(f"Index {key} out of range") from err

                # If unsafe, use direct set by creating a new array
                # noinspection PyProtectedMember
                start_addr = ctypes.addressof(self._pyobject._ob_item_0)
                # Size should be higher of the current size and the index
                size = max(self.size, key + 1)
                arr = (Py_ssize_t * size).from_address(start_addr)
                arr[key] = new_ref(value)

    def __len__(self) -> int:
        return self.size

    @property
    def item(self) -> Array[Py_ssize_t]:
        return self._pyobject.ob_item

    @item.setter
    def item(self, value: Array) -> None:
        if not self._unsafe:
            raise UnsafeAttributeError.from_attr("item")
        self._pyobject.ob_item = value


class IntView(VarView[_T]):
    _pyobject: PyLongObject

    @property
    def digits(self) -> Array[Py_ssize_t]:
        return self._pyobject.ob_digit

    @digits.setter
    def digits(self, value: Iterable) -> None:
        self._pyobject.ob_digit[:] = value

    @property
    def value(self) -> int:
        return self._pyobject.value

    @value.setter
    def value(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError(f"Expected int, got {type(value).__name__!r}")
        # Get a struct of the new value
        cls = type(self._pyobject)
        new_val = cls.from_object(value)

        # The new value's ob_size must be equal or less than the current
        new_size = abs(new_val.ob_size)
        cur_size = abs(self._pyobject.ob_size)
        if new_size > cur_size:
            raise ValueError(f"New value {value!r} too large")

        # Copy the new value's digits into the current value
        self.digits[:new_size] = new_val.ob_digit

        # Set the new value's ob_size
        self._pyobject.ob_size = new_size
