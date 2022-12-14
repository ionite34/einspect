"""Python version compatibility constructs."""
from __future__ import annotations

import sys
import typing
from collections import abc
from dataclasses import dataclass
from enum import Enum
from typing import Generic, NoReturn, TypeVar

__all__ = ("Version", "RequiresPythonVersion", "python_req", "python_above", "abc")

if sys.version_info > (3, 8):
    abc = typing  # noqa: F401, F811


class Version(Enum):
    """Python version constants."""

    PY_3_7 = (3, 7)
    PY_3_8 = (3, 8)
    PY_3_9 = (3, 9)
    PY_3_10 = (3, 10)


_V = TypeVar("_V", bound=Version)


@dataclass
class RequiresPythonVersion(Generic[_V]):
    version: _V

    def __call__(self, *args, **kwargs) -> NoReturn:
        raise RuntimeError(
            f"Requires Python {self.version.value[0]}.{self.version.value[1]}"
        )

    def __getitem__(self, _item) -> RequiresPythonVersion[_V]:
        return self


def python_req(version: _V) -> RequiresPythonVersion[_V] | None:
    """
    Returns None if equal or greater than current Python version.

    If lower, returns an 'RequiresPythonVersion' instance.
    """
    if sys.version_info < version.value:  # type: ignore
        return RequiresPythonVersion(version)
    return None


def python_above(version: Version) -> bool:
    """Returns True if equal or greater than current Python version."""
    return sys.version_info >= version.value
