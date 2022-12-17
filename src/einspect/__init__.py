from typing import ContextManager

from einspect.views import unsafe as _unsafe
from einspect.views.factory import view

__all__ = ["view", "unsafe"]

unsafe: ContextManager[None] = _unsafe.Context.unsafe
