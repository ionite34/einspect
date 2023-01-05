"""View formatted info implementation."""
from __future__ import annotations

# noinspection PyUnresolvedReferences, PyProtectedMember
from ctypes import pointer, _Pointer, Array
from string import Template
from typing import TYPE_CHECKING, Any

from einspect.structs.py_object import PyObject

if TYPE_CHECKING:
    from einspect.views.view_base import View

BASE = Template("$struct_name (at $address):")
INDENTS_COUNT = 3
INDENTS = " " * INDENTS_COUNT

# Display transforms for types
DISP_TRANSFORMS = {
    type: lambda c: c.__name__,
}


def format_value(obj: Any) -> str:
    """Format a value."""
    # Array: format as list
    if isinstance(obj, Array):
        res = list(map(format_value, obj))
        return f"[{', '.join(res)}]"
    # For pointers, get the value
    if isinstance(obj, _Pointer):
        val = format_value(obj.contents) if obj else "NULL"
        wrap = f"[{val}]" if not (val.startswith("[") and val.endswith("]")) else val
        return f"&{wrap}"
    # For PyObject, get the object
    if isinstance(obj, PyObject):
        obj.IncRef()
        return format_value(obj.into_object().value)
    # Other cases
    try:
        return DISP_TRANSFORMS[type(obj)](obj)
    except KeyError:
        return repr(obj)


def format_attr(struct: PyObject, attr: str, hint: str, types: bool) -> str:
    value = getattr(struct, attr)
    type_str = f": {hint}" if types else ""
    res = f"{attr}{type_str} = {format_value(value)}"
    return res


def indent(s: str) -> str:
    """Indent a string."""
    return INDENTS + s


# noinspection PyProtectedMember
def format_display(v: View, types: bool = True) -> str:
    lines = []
    # Get struct
    struct = v._pyobject
    struct_name = struct.__class__.__name__
    address = f"0x{struct.address:x}"
    # Make line 1
    lines.append(BASE.substitute(struct_name=struct_name, address=address))

    # Get attributes
    for attr, type_hint in struct._format_fields_().items():
        lines.append(
            indent(format_attr(struct, attr, type_hint, types))
        )

    return "\n".join(lines)
