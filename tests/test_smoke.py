"""
Smoke tests — verifies the package installs and imports correctly.
These run on every PR via GitHub Actions CI.
"""

import sidecar


def test_package_importable():
    """CI gate: package must import without errors."""
    assert sidecar is not None


def test_version_string():
    """CI gate: version string must be present and non-empty."""
    assert hasattr(sidecar, "__version__")
    assert isinstance(sidecar.__version__, str)
    assert len(sidecar.__version__) > 0
