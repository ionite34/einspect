"""Python version compatibility constructs."""
from __future__ import annotations

import sys
from ctypes import pythonapi, PyDLL
from enum import Enum
from typing import Generic, TypeVar, NoReturn


class Version(Enum):
    PY_3_9 = (3, 9)
    PY_3_10 = (3, 10)


_V = TypeVar("_V", bound=Version)


class RequiresPythonVersion(Generic[_V]):
    def __init__(self, version: _V) -> None:
        self.version: _V = version

    def __call__(self, *args, **kwargs) -> NoReturn:
        raise RuntimeError(f"Requires Python {self.version.value[0]}.{self.version.value[1]}")

    def __getitem__(self, _item) -> NoReturn:
        return self


def pythonapi_req(version: _V) -> RequiresPythonVersion[_V] | PyDLL:
    """
    Get a function from pythonapi with a required minimum python version.

    If lower, returns an 'RequiresPythonVersion' instance.
    """
    if sys.version_info < version.value:  # type: ignore
        return RequiresPythonVersion(version)
    return pythonapi
