from __future__ import annotations

from contextlib import suppress
from ctypes import addressof, c_void_p, memmove
from typing import TYPE_CHECKING

from einspect.api import PTR_SIZE
from einspect.errors import UnsafeError
from einspect.structs import PyASCIIObject, PyObject, TpFlags

if TYPE_CHECKING:
    from einspect.views.view_base import View


def check_move(dst: View, src: View) -> None:
    """
    Check if a memory from `dst` to `src` is safe.

    Raises:
        UnsafeError: If the move is unsafe.
    """
    # If non-gc type into gc type, always unsafe
    if not src.is_gc() and dst.is_gc():
        raise UnsafeError(
            f"Move of non-gc type {src.type.__name__!r} into gc type"
            f" {dst.type.__name__!r} requires an unsafe context."
        )

    dst_allocated = dst.mem_allocated
    dst_offset = 0

    # Check if dst has an instance dict
    if (dst_dict := dst._pyobject.instance_dict()) is not None:
        # Set -1 to if managed dict
        if dst._pyobject.ob_type.contents.tp_flags & TpFlags.MANAGED_DICT:
            dst_offset = -1
        else:
            # If offset is positive, add this to dst_allocated
            dst_offset = addressof(dst_dict) - dst._pyobject.address
            if dst_offset > 0:
                dst_allocated = max((dst_offset + PTR_SIZE), dst_allocated)

    # Check if we need to move an instance dict
    if (src_dict := src._pyobject.instance_dict()) is not None:
        # If moving from managed -> managed, always safe
        if not (
            src._pyobject.ob_type.contents.tp_flags & TpFlags.MANAGED_DICT
            and dst_offset == -1
        ):
            src_offset = addressof(src_dict) - src._pyobject.address
            # If negative, it must match dst_offset
            neg_unsafe = src_offset < 0 and src_offset != dst_offset
            # Otherwise, needs to be within mem_allocated
            pos_unsafe = src_offset > 0 and (src_offset + PTR_SIZE) > dst_allocated
            if neg_unsafe or pos_unsafe:
                raise UnsafeError(
                    f"memory move of instance dict at offset {src_offset} from {src.type.__name__!r} "
                    f"to {dst.type.__name__!r} is out of bounds. Enter an unsafe context to allow this."
                )

    # Check if src mem_size can fit into dst mem_allocated
    if src.mem_size > dst_allocated:
        raise UnsafeError(
            f"memory move of {src.mem_size} bytes into allocated space of {dst.mem_allocated} bytes"
            " is out of bounds. Enter an unsafe context to allow this."
        )


def move(
    dst: PyObject, src: PyObject, offset: int = PTR_SIZE, inst_dict: bool = True
) -> None:
    """Move data from PyObjects `src` to `dst`."""
    # If either is a string, un-intern them
    for py_obj in (src, dst):
        if isinstance(py_obj, PyASCIIObject):
            py_obj: PyASCIIObject
            py_obj.interned = 0  # not interned
            py_obj.hash = -1  # invalidate cached hash

    # Materialize instance dicts in case we need to copy
    src_dict_ptr = None
    if inst_dict:
        with suppress(AttributeError):
            src.GetAttr("__dict__")
        with suppress(AttributeError):
            dst.GetAttr("__dict__")

        if (src_dict_ptr := src.instance_dict()) is not None:
            dict_addr = addressof(src_dict_ptr)
            # Normally we copy by offset, unless managed dict
            if not src.ob_type.contents.tp_flags & TpFlags.MANAGED_DICT:
                dict_offset = dict_addr - src.address
                memmove(
                    dst.address + dict_offset,
                    c_void_p(dict_addr),
                    PTR_SIZE,
                )

    # Move main object
    memmove(
        dst.address + offset,
        src.address + offset,
        src.mem_size - offset,
    )

    # For managed dicts, we materialize the dict after move to copy it
    if (
        inst_dict
        and src_dict_ptr is not None
        and src.ob_type.contents.tp_flags & TpFlags.MANAGED_DICT
    ):
        dst.SetAttr("__dict__", src_dict_ptr.contents.into_object())
