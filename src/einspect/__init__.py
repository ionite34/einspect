from __future__ import annotations

from typing import ContextManager

from einspect.views.factory import view
from einspect.views.unsafe import UnsafeContext
from einspect.views.view_base import View

__all__ = ["view", "unsafe"]

unsafe: ContextManager[None] = UnsafeContext.unsafe
