from __future__ import annotations

from typing import ContextManager

# Runtime patches
import einspect._patch
from einspect.type_orig import orig
from einspect.types import NULL, ptr
from einspect.views.factory import view
from einspect.views.unsafe import global_unsafe
from einspect.views.view_type import impl

einspect._patch.run()

__all__ = ("view", "unsafe", "impl", "orig", "ptr", "NULL")

__version__ = "0.5.0"

unsafe: ContextManager[None] = global_unsafe
