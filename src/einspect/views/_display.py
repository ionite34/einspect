"""View formatted info implementation."""
from __future__ import annotations

import ctypes
from ctypes import Array
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


def format_value(
    obj: Any, cast_to: type | None = None, arr_bound: int | None = None
) -> str:
    """
    Format a value.

    Args:
        obj: The value to format
        cast_to: The type to cast the value to
        arr_bound: The max number of pointers to dereference for Array[PyObject] types
    """
    # Cast if needed
    if cast_to is not None:
        obj = ctypes.cast(obj, cast_to)  # type: ignore
        return format_value(obj)
    # Array: format as list
    if isinstance(obj, Array):
        # Only get elements up to arr_bound
        res = list(map(format_value, obj[:arr_bound]))
        diff = len(obj) - len(res)
        return f"[{', '.join(res)}{', ...' if diff > 0 else ''}]"
    # For pointers, get the value
    # noinspection PyUnresolvedReferences, PyProtectedMember
    if isinstance(obj, ctypes._Pointer):
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


def format_attr(
    struct: PyObject, attr: str, hint: str | tuple[str, type], types: bool
) -> str:
    value = getattr(struct, attr)
    type_cast = None
    if isinstance(hint, tuple):
        hint, type_cast = hint
    type_str = f": {hint}" if types else ""
    res = f"{attr}{type_str} = {format_value(value, cast_to=type_cast)}"
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
        lines.append(indent(format_attr(struct, attr, type_hint, types)))

    return "\n".join(lines)
