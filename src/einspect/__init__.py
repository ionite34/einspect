from __future__ import annotations

from typing import ContextManager

from einspect.type_orig import orig
from einspect.views.factory import view
from einspect.views.unsafe import global_unsafe
from einspect.views.view_type import impl

__all__ = ("view", "unsafe", "impl", "orig")

unsafe: ContextManager[None] = global_unsafe
