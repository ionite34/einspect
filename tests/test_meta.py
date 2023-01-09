from __future__ import annotations

import importlib
import inspect
import pkgutil
from types import ModuleType

import pytest

from einspect import views
from einspect.views import factory


def pkg_names(pkg: ModuleType) -> list[str]:
    """Return all module names in a module."""
    return [name for _, name, _ in pkgutil.iter_modules(pkg.__path__)]


def pkg_class(pkg: ModuleType):
    """Return the first class in a module."""
    for _, obj in inspect.getmembers(pkg):
        if inspect.isclass(obj):
            return obj
    raise ValueError(f"Module {pkg} has no classes.")


@pytest.mark.parametrize(
    "mod_name",
    filter(
        lambda x: x.startswith("view_") and not x.endswith("_base"), pkg_names(views)
    ),
)
def test_views_modules(mod_name: str):
    """Test that factory supports all views."""
    module = importlib.import_module(f"einspect.views.{mod_name}")
    m_dict = module.__dict__
    # Check all views have __all__
    if "__all__" not in m_dict:
        pytest.fail(f"Module {module.__name__} has no __all__.")

    # Check view classes defined in factory mapping
    view_type = getattr(module, m_dict["__all__"][0])
    assert view_type in factory.VIEW_TYPES.values()
