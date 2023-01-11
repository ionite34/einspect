from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, TypeVar

from typing_extensions import Self

from einspect.compat import Version, python_above
from einspect.errors import UnsafeError
from einspect.structs.include.object_h import TpFlags
from einspect.structs.py_type import PyTypeObject
from einspect.structs.slots_map import Slot, get_slot
from einspect.views.view_base import REF_DEFAULT, VarView

__all__ = ("TypeView",)

_T = TypeVar("_T")


class TypeView(VarView[_T, None, None]):
    _pyobject: PyTypeObject[_T]

    def __init__(self, obj: _T, ref: bool = REF_DEFAULT) -> None:
        super().__init__(obj, ref)
        self._store = []

    @property
    def immutable(self) -> bool:
        """Return True if the type is immutable."""
        if python_above(Version.PY_3_10):
            return bool(self._pyobject.tp_flags & TpFlags.IMMUTABLETYPE)
        return not bool(self._pyobject.tp_flags & TpFlags.HEAPTYPE)

    @immutable.setter
    def immutable(self, value: bool):
        """Set whether the type is immutable."""
        if python_above(Version.PY_3_10):
            if value:
                self._pyobject.tp_flags |= TpFlags.IMMUTABLETYPE
            else:
                self._pyobject.tp_flags &= ~TpFlags.IMMUTABLETYPE
        else:
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
        yield self
        self.immutable = True

    def _try_alloc(self, slot: Slot):
        # Check if there is a ptr class
        if slot.ptr_type is None:
            return
        # Check if the slot is a null pointer
        ptr = getattr(self._pyobject, slot.parts[0])
        if not ptr:
            # Make a new ptr type struct
            new = slot.ptr_type()
            ptr.contents = new

    def __getitem__(self, key):
        """Get an attribute from the type object."""
        return self._pyobject.GetAttr(key)

    def __setitem__(self, key, value):
        """Set an attribute on the type object."""
        # Check if this is a slots attr
        if slot := get_slot(key):
            # Allocate sub-struct if needed
            self._try_alloc(slot)

        with self.as_mutable():
            self._pyobject.Modified()
            self._pyobject.SetAttr(key, value)

        # Invalidate type lookup cache
        self._pyobject.Modified()

    def __getattr__(self, item: str):
        # Forward `tp_` attributes from PyTypeObject
        if item.startswith("tp_"):
            return getattr(self._pyobject, item)
        raise AttributeError(item)

    def __setattr__(self, key: str, value: Any) -> None:
        # Forward `tp_` attributes from PyTypeObject
        if key.startswith("tp_") and hasattr(self._pyobject, key):
            if not self._unsafe:
                raise UnsafeError(
                    f"Setting attribute {key} requires an unsafe context."
                )
            setattr(self._pyobject, key, value)
            return
        super().__setattr__(key, value)
