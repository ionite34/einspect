"""Python version compatibility constructs."""
from __future__ import annotations

import sys
import typing
from collections import abc
from dataclasses import dataclass
from enum import Enum
from typing import Generic, NoReturn, TypeVar

__all__ = ("Version", "RequiresPythonVersion", "python_req", "abc")

if sys.version_info > (3, 8):
    abc = typing  # noqa: F401, F811


class Version(Enum):
    """Python version constants."""

    PY_3_7 = (3, 7)
    PY_3_8 = (3, 8)
    PY_3_9 = (3, 9)
    PY_3_10 = (3, 10)
    PY_3_11 = (3, 11)
    PY_3_12 = (3, 12)

    def above(self, or_eq: bool = True) -> bool:
        """Return whether the current version is above this version."""
        if or_eq:
            return sys.version_info >= self.value
        return sys.version_info > self.value

    def below(self, or_eq: bool = False) -> bool:
        """Return whether the current version is below this version."""
        if or_eq:
            return sys.version_info <= self.value
        return sys.version_info < self.value

    def req_above(self, or_eq: bool = True) -> RequiresPythonVersion | None:
        """Return None if above a python version, else a RequiresPythonVersion instance."""
        return None if self.above(or_eq) else RequiresPythonVersion(self)

    def req_below(self, or_eq: bool = False) -> RequiresPythonVersion | None:
        """Return None if below a python version, else a RequiresPythonVersion instance."""
        return None if self.below(or_eq) else RequiresPythonVersion(self)


_V = TypeVar("_V", bound=Version)


@dataclass
class RequiresPythonVersion(Generic[_V]):
    version: _V

    def __msg__(self) -> str:
        return f"Requires Python {self.version.value[0]}.{self.version.value[1]}"

    def __call__(self, *args, **kwargs) -> NoReturn:
        raise RuntimeError(self.__msg__())

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
