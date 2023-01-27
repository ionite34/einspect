from __future__ import annotations

from collections.abc import Callable
from types import BuiltinFunctionType
from typing import Any, TypeVar

from einspect.structs import PyCFunctionObject
from einspect.structs.include.methodobject_h import PyMethodDef
from einspect.structs.include.object_h import vectorcallfunc
from einspect.structs.py_object import py_get, py_set
from einspect.structs.traits import IsGC
from einspect.views.unsafe import unsafe
from einspect.views.view_base import View

__all__ = ("CFunctionView",)

_T = TypeVar("_T", BuiltinFunctionType, Callable)


class CFunctionView(View[_T, None, None], IsGC):
    _pyobject: PyCFunctionObject[_T]

    def __init__(self, obj: _T, ref: bool = False) -> None:
        super().__init__(obj, ref)

    @property
    def ml(self) -> PyMethodDef:
        return self._pyobject.m_ml.contents

    # noinspection PyPropertyDefinition, PyMethodParameters
    @property
    def self(__self):
        return py_get(__self._pyobject.m_self)

    # noinspection PyPropertyDefinition, PyMethodParameters
    @self.setter
    @unsafe
    def self(__self, value):
        """Passed as 'self' arg to the C func."""
        py_set(__self._pyobject.m_self, value)

    @property
    def module(self) -> str:
        """The __module__ attribute, can be anything."""
        return self._pyobject.m_module.contents.into_object()

    @module.setter
    def module(self, value: str) -> None:
        py_set(self._pyobject.m_module, value)

    @property
    def weakreflist(self) -> Any:
        """Weak reference list"""
        return self._pyobject.m_weakreflist.contents.into_object()

    @weakreflist.setter
    def weakreflist(self, value: Any) -> None:
        py_set(self._pyobject.m_weakreflist, value)

    @property
    def vectorcall(self) -> vectorcallfunc:
        """Vectorcall function"""
        return self._pyobject.vectorcall

    @vectorcall.setter
    @unsafe
    def vectorcall(self, value: Callable) -> None:
        self._pyobject.vectorcall = vectorcallfunc(value)
