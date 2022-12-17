from einspect.views import unsafe as _unsafe
from einspect.views.factory import view

__all__ = ["view", "unsafe"]

unsafe = _unsafe.Context.unsafe
