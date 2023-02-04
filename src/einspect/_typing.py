import types
from typing import Any, Union, get_origin


def is_union(obj: Any) -> bool:
    """Checks if the type is a Union or UnionType (3.10+)."""
    if not hasattr(obj, "__args__"):
        return False
    if getattr(types, "UnionType", None):
        return get_origin(obj) in (Union, types.UnionType)
    return get_origin(obj) is Union
