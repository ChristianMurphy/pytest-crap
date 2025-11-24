def test_version_available() -> None:
    import pytest_crap

    assert hasattr(pytest_crap, "__version__")
    assert isinstance(pytest_crap.__version__, str)
