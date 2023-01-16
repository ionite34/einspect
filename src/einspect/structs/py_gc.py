from __future__ import annotations

from ctypes import Structure, c_void_p, cast
from enum import IntEnum

from typing_extensions import Annotated

from einspect.api import uintptr_t
from einspect.structs.deco import struct
from einspect.structs.traits import AsRef
from einspect.types import ptr


class PyGC(IntEnum):
    """Bit flags for _gc_prev"""

    # Bit 0 is set when tp_finalize is called
    PREV_MASK_FINALIZED = 1
    # Bit 1 is set when the object is in generation which is GCed currently.
    PREV_MASK_COLLECTING = 2
    # The (N-2) most significant bits contain the real address.
    PREV_SHIFT = 2
    PREV_MASK = uintptr_t(-1).value << PREV_SHIFT


@struct
class PyGC_Head(Structure, AsRef):
    """
    Defines the PyGC_Head Structure.

    GC information is stored BEFORE the object structure.
    https://github.com/python/cpython/blob/3.11/Include/internal/pycore_gc.h#L11-L20
    """

    # Pointer to next object in the list.
    # 0 means the object is not tracked
    _gc_next: Annotated[int, uintptr_t]
    # Pointer to previous object in the list.
    # Lowest two bits are used for flags.
    _gc_prev: Annotated[int, uintptr_t]

    def Next(self) -> ptr[PyGC_Head]:
        return cast(self._gc_next, ptr[PyGC_Head])

    def Set_Next(self, item: ptr[PyGC_Head]) -> None:
        addr = cast(item, c_void_p).value
        self._gc_next = addr

    def Prev(self) -> ptr[PyGC_Head]:
        return cast(self._gc_prev & PyGC.PREV_MASK, ptr[PyGC_Head])

    def Set_Prev(self, item: ptr[PyGC_Head]) -> None:
        item = cast(item, c_void_p).value
        if item & ~PyGC.PREV_MASK != 0:
            raise ValueError("item is not valid")
        self._gc_prev = (self._gc_prev & ~PyGC.PREV_MASK) | item

    def Finalized(self) -> bool:
        return (self._gc_prev & PyGC.PREV_MASK_FINALIZED) != 0

    def Set_Finalized(self) -> None:
        self._gc_prev |= PyGC.PREV_MASK_FINALIZED
