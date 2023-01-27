from __future__ import annotations

from collections.abc import Callable
from types import CodeType, FunctionType
from typing import Any, Dict

from einspect.compat import Version
from einspect.structs import PyFunctionObject
from einspect.structs.include.object_h import vectorcallfunc
from einspect.structs.py_object import py_get, py_set
from einspect.structs.traits import IsGC
from einspect.views.unsafe import unsafe
from einspect.views.view_base import View

__all__ = ("FunctionView",)


class FunctionView(View[FunctionType, None, None], IsGC):
    _pyobject: PyFunctionObject

    def __init__(self, obj: FunctionType | Callable, ref: bool = False) -> None:
        super().__init__(obj, ref)

    @property
    def globals(self) -> Dict[str, Any]:
        return self._pyobject.globals.contents.into_object()

    @globals.setter
    @unsafe
    def globals(self, value: Dict[str, Any]) -> None:
        py_set(self._pyobject.globals, value)

    @property
    def builtins(self) -> Dict[str, Any]:
        if Version.PY_3_10.below():
            raise AttributeError(
                "PyFunctionObject does not have builtins below Python 3.10"
            )
        return self._pyobject.builtins.contents.into_object()

    @builtins.setter
    @unsafe
    def builtins(self, value: Dict[str, Any]) -> None:
        if Version.PY_3_10.below():
            raise AttributeError(
                "PyFunctionObject does not have builtins below Python 3.10"
            )
        py_set(self._pyobject.builtins, value)

    @property
    def name(self) -> str:
        return self._pyobject.name.contents.into_object()

    @name.setter
    def name(self, value: str) -> None:
        py_set(self._pyobject.name, value)

    @property
    def qualname(self) -> str:
        return self._pyobject.qualname.contents.into_object()

    @qualname.setter
    def qualname(self, value: str) -> None:
        py_set(self._pyobject.qualname, value)

    @property
    def code(self) -> CodeType:
        return self._pyobject.code.contents.into_object()

    @code.setter
    def code(self, value: CodeType) -> None:
        py_set(self._pyobject.code, value)

    @property
    def defaults(self) -> tuple[Any, ...] | None:
        return py_get(self._pyobject.defaults)

    @defaults.setter
    def defaults(self, value: tuple[Any, ...] | None) -> None:
        py_set(self._pyobject.defaults, value)

    @property
    def kwdefaults(self) -> Dict[str, Any] | None:
        return py_get(self._pyobject.kwdefaults)

    @kwdefaults.setter
    def kwdefaults(self, value: Dict[str, Any] | None) -> None:
        py_set(self._pyobject.kwdefaults, value)

    @property
    def closure(self) -> tuple[Any, ...] | None:
        return py_get(self._pyobject.closure)

    @closure.setter
    @unsafe
    def closure(self, value: tuple[Any, ...] | None) -> None:
        py_set(self._pyobject.closure, value)

    @property
    def doc(self) -> str | None:
        return self._pyobject.func_doc.contents.into_object()

    @doc.setter
    def doc(self, value: str | None) -> None:
        py_set(self._pyobject.func_doc, value)

    @property
    def dict(self) -> Dict[str, Any] | None:
        return py_get(self._pyobject.func_dict)

    @dict.setter
    def dict(self, value: Dict[str, Any] | None) -> None:
        py_set(self._pyobject.func_dict, value)

    @property
    def weakreflist(self) -> list[Any]:
        return self._pyobject.func_weakreflist.contents.into_object()

    @weakreflist.setter
    @unsafe
    def weakreflist(self, value: list[Any]) -> None:
        py_set(self._pyobject.func_weakreflist, value)

    @property
    def module(self) -> str:
        return self._pyobject.func_module.contents.into_object()

    @module.setter
    def module(self, value: str) -> None:
        py_set(self._pyobject.func_module, value)

    @property
    def annotations(self) -> Dict[str, Any] | None:
        return py_get(self._pyobject.func_annotations)

    @annotations.setter
    def annotations(self, value: Dict[str, Any] | None) -> None:
        py_set(self._pyobject.func_annotations, value)

    @property
    def vectorcall(self) -> Callable:
        return self._pyobject.vectorcall.contents.into_object()

    @vectorcall.setter
    @unsafe
    def vectorcall(self, value: Callable) -> None:
        self._pyobject.vectorcall = vectorcallfunc(value)

    @property
    def version(self) -> int:
        if Version.PY_3_11.below():
            raise AttributeError(
                "PyFunctionObject does not have version below Python 3.11"
            )
        return self._pyobject.func_version

    @version.setter
    @unsafe
    def version(self, value: int) -> None:
        if Version.PY_3_11.below():
            raise AttributeError(
                "PyFunctionObject does not have version below Python 3.11"
            )
        self._pyobject.func_version = value
