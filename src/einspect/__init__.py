from __future__ import annotations

import einspect._patch
from einspect.type_orig import orig
from einspect.types import NULL, ptr
from einspect.views.factory import view
from einspect.views.unsafe import global_unsafe
from einspect.views.view_type import impl

__all__ = ("view", "unsafe", "impl", "orig", "ptr", "NULL", "__version__")
__version__ = "0.5.16"

unsafe = global_unsafe

# Runtime patches
einspect._patch.run()
