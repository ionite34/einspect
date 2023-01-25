"""View formatted info implementation."""
from __future__ import annotations

import ctypes
from ctypes import Array, Structure, cast
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


def indent(s: str) -> str:
    """Indent a string."""
    # For single line strings, just add indents
    if "\n" not in s:
        return INDENTS + s
    # For multi-line, add indents to each line
    return "\n".join(INDENTS + line for line in s.splitlines())


class Formatter:
    def __init__(self, types: bool = True, arr_max: int | None = None):
        """
        Initialize a Formatter.

        Args:
            types: Whether to include type hints.
            arr_max: The max number of elements to show for Array types.
        """
        self.types = types
        self.arr_max = arr_max

    def format_value(self, obj: Any) -> str:
        """Format a value."""
        # Array: format as list
        if isinstance(obj, Array):
            # If there is a max, limit the number of elements
            diff = 0
            if self.arr_max is not None and len(obj) > self.arr_max:
                diff = len(obj) - self.arr_max
                obj = obj[: self.arr_max]
            res = list(map(self.format_value, obj))

            # For structures (first char is \n), add \n to last and indent
            if res and res[0].startswith("{ ") and res[0].endswith(" }"):
                sep = f",\n{INDENTS}"
                text = f"{sep.join(res)}{', ...' if diff > 0 else ''}"
                return f"[\n{INDENTS}{text}\n]"

            return f"[{', '.join(res)}{', ...' if diff > 0 else ''}]"
        # For pointers, get the value
        # noinspection PyUnresolvedReferences, PyProtectedMember
        if isinstance(obj, ctypes._Pointer):
            val = self.format_value(obj.contents) if obj else "NULL"
            if val.startswith("[") and val.endswith("]"):
                return f"&{val}"
            return f"&[{val}]"
        # For PyObject, get the object
        if isinstance(obj, PyObject):
            obj.IncRef()
            return self.format_value(obj.into_object())
        # For ctypes Structures, do multi-line formatting
        if isinstance(obj, Structure):
            return self.format_structure(obj, short=True)
        # Other cases
        try:
            return DISP_TRANSFORMS[type(obj)](obj)
        except KeyError:
            # Fallback to repr
            return repr(obj)

    def format_attr(
        self,
        struct: PyObject,
        attr: str,
        hint: str | tuple[str, type],
        type_hints: bool | None = None,
    ) -> str:
        value = getattr(struct, attr)
        type_cast = None
        if isinstance(hint, tuple):
            hint, type_cast = hint

        use_hints = self.types if type_hints is None else type_hints
        type_str = f": {hint}" if use_hints else ""

        # If cast_to provided
        if type_cast is not None:
            value = cast(value, type_cast)
            value = getattr(value, "value", value)

        res = f"{attr}{type_str} = {self.format_value(value)}"
        return res

    # noinspection PyProtectedMember
    def format_structure(self, struct: Structure, short: bool | None = None) -> str:
        # Short mode looks like
        # { ob_refcnt = 1, ob_type = &[object] }
        lines = []
        # Auto short if below 5
        if short is None:
            short = len(struct._format_fields_()) < 5
        # Get attributes
        for attr, type_hint in struct._format_fields_().items():
            text = self.format_attr(
                struct=struct,
                attr=attr,
                hint=type_hint,
                # If short, don't show type hints
                type_hints=(None if not short else False),
            )
            if not short:
                text = indent(text)
            lines.append(text)
        if short:
            return f"{{ {', '.join(lines)} }}"
        return "\n" + "\n".join(lines) + "\n"

    # noinspection PyProtectedMember
    def format_view(self, v: View) -> str:
        """Format a display string for a View."""
        lines = []
        # Get struct
        struct = v._pyobject
        struct_name = struct.__class__.__name__
        address = f"0x{struct.address:x}"
        # Make line 1
        lines.append(BASE.substitute(struct_name=struct_name, address=address))
        # Get attributes
        for attr, type_hint in struct._format_fields_().items():
            lines.append(indent(self.format_attr(struct, attr, type_hint)))

        return "\n".join(lines)
