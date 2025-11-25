"""Unit tests for __init__ module.

Uses importlib.reload() to ensure coverage captures the import-time code,
since the plugin is loaded by pytest before coverage starts.
"""

from __future__ import annotations

import importlib


def test_version_is_string() -> None:
    """Test that __version__ is a string."""
    import pytest_crap

    importlib.reload(pytest_crap)

    assert isinstance(pytest_crap.__version__, str)


def test_version_format() -> None:
    """Test that __version__ follows semver format."""
    import pytest_crap

    importlib.reload(pytest_crap)

    parts = pytest_crap.__version__.split(".")
    assert len(parts) == 3
    # Should be parseable as integers
    major, minor, patch = parts
    assert major.isdigit()
    assert minor.isdigit()
    assert patch.isdigit()
