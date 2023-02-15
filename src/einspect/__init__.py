from __future__ import annotations

import einspect._patch
from einspect.type_orig import orig
from einspect.types import NULL, ptr
from einspect.views.factory import view
from einspect.views.unsafe import global_unsafe
from einspect.views.view_type import impl

# Runtime patches
einspect._patch.run()

__all__ = ("view", "unsafe", "impl", "orig", "ptr", "NULL")

__version__ = "0.5.11"

unsafe = global_unsafe
