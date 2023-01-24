from __future__ import annotations

from ctypes import addressof
from typing import TYPE_CHECKING

from einspect.api import PTR_SIZE
from einspect.errors import UnsafeError

if TYPE_CHECKING:
    from einspect.views.view_base import View


def _check_move(dst: View, src: View) -> None:
    """
    Check if the string can be resized to `target` size.

    Raises:
        UnsafeError: If the string cannot be resized, and not in an unsafe context.
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
        # If offset is positive, add this to dst_allocated
        dst_offset = addressof(dst_dict) - dst._pyobject.address
        if dst_offset > 0:
            dst_allocated = max((dst_offset + PTR_SIZE), dst_allocated)

    # Check if we need to move an instance dict
    if (src_dict := src._pyobject.instance_dict()) is not None:
        src_offset = addressof(src_dict) - src._pyobject.address
        # If negative, it must match dst_offset
        if src_offset < 0 and src_offset != dst_offset:
            raise UnsafeError(
                f"Move of instance dict from {src.type.__name__!r} to {dst.type.__name__!r}"
                " requires an unsafe context."
            )
        # Otherwise, needs to be within mem_allocated
        if src_offset > 0 and (src_offset + PTR_SIZE) > dst_allocated:
            raise UnsafeError(
                f"Move of instance dict from {src.type.__name__!r} to {dst.type.__name__!r}"
                " requires an unsafe context."
            )

    # Check if src mem_size can fit into dst mem_allocated
    if src.mem_size > dst_allocated:
        raise UnsafeError(
            f"memory move of {src.mem_size} bytes into allocated space of {dst.mem_allocated} bytes"
            " is out of bounds. Enter an unsafe context to allow this."
        )
