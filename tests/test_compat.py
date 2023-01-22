from unittest.mock import patch

import pytest

from einspect.compat import RequiresPythonVersion, Version, python_req


# Patch our python version to be 3.9
@patch("einspect.compat.sys.version_info", (3, 9))
def test_python_req_lower() -> None:
    """Lower than required version returns RequiresPythonVersion."""
    assert python_req(Version.PY_3_9) is None
    assert python_req(Version.PY_3_10) == RequiresPythonVersion(Version.PY_3_10)
    assert Version.PY_3_9.req_below(or_eq=True) is None
    assert Version.PY_3_9.req_below() == RequiresPythonVersion(Version.PY_3_9)
    assert Version.PY_3_8.req_above() is None
    assert Version.PY_3_9.req_above(or_eq=False) == RequiresPythonVersion(
        Version.PY_3_9
    )


def test_requires_python_version_obj() -> None:
    """RequiresPythonVersion object methods."""
    req = RequiresPythonVersion(Version.PY_3_7)
    assert req.__msg__() == "Requires Python 3.7"
    # Getitem should return self
    assert req[1] is req
    assert req["abc"] is req
    # Call should raise
    with pytest.raises(RuntimeError) as exc:
        req()


def test_python_req_ok() -> None:
    """Supported version checks returns None."""
    assert python_req(Version.PY_3_7) is None
    assert Version.PY_3_7.req_above() is None
