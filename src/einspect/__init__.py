from einspect.views.factory import view
from einspect.views import unsafe as _unsafe

__all__ = ["view", "unsafe"]

unsafe = _unsafe.Context.unsafe
