from unittest.mock import patch

from einspect.compat import RequiresPythonVersion, Version, python_req


# Patch our python version to be 3.9
@patch("einspect.compat.sys.version_info", (3, 9))
def test_python_req_lower() -> None:
    """Lower than required version returns RequiresPythonVersion."""
    assert python_req(Version.PY_3_10) == RequiresPythonVersion(Version.PY_3_10)


def test_python_req_ok() -> None:
    """Supported version checks returns None."""
    assert python_req(Version.PY_3_7) is None
