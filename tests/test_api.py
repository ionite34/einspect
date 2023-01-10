import sys
from ctypes import pythonapi

from einspect.api import Py
from einspect.compat import RequiresPythonVersion, Version
from tests import get_addr


def test_compat_new_ref() -> None:
    """NewRef method is present."""
    assert hasattr(Py, "NewRef")
    # Actual api should exist in >= 3.10
    if sys.version_info >= (3, 10):
        assert get_addr(Py.NewRef) == get_addr(pythonapi["Py_NewRef"])
    else:
        assert Py.NewRef == RequiresPythonVersion(Version.PY_3_10)
