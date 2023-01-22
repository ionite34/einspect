from __future__ import annotations

from einspect.api import address
from einspect.structs import PyBoolObject
from einspect.views.view_int import IntView

__all__ = ("BoolView",)


class BoolView(IntView):
    _pyobject: PyBoolObject

    @property
    def mem_size(self) -> int:
        # If used on the singletons, use their
        addr = self._pyobject.address
        if addr == address(True):
            return True.__sizeof__()
        elif addr == address(False):
            return False.__sizeof__()
        return super().mem_size
