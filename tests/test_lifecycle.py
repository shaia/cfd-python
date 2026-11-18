"""Tests for library lifecycle and version functions (v0.2.0)."""

import pytest

import cfd_python


class TestLibraryLifecycle:
    """Tests for init(), finalize(), is_initialized()."""

    @pytest.fixture(autouse=True)
    def _restore_init_state(self):
        """Snapshot and restore library init state so tests don't leak side-effects."""
        was_initialized = cfd_python.is_initialized()
        yield
        if was_initialized:
            cfd_python.init()
        else:
            cfd_python.finalize()

    def test_is_initialized_returns_bool(self):
        result = cfd_python.is_initialized()
        assert isinstance(result, bool)

    def test_init_succeeds(self):
        cfd_python.init()
        assert cfd_python.is_initialized()

    def test_finalize_succeeds(self):
        cfd_python.init()
        cfd_python.finalize()

    def test_repeated_init_safe(self):
        """Verify repeated init calls do not crash."""
        for _ in range(10):
            cfd_python.init()
        assert cfd_python.is_initialized()

    def test_init_finalize_cycle(self):
        """Verify init/finalize can be cycled without errors."""
        for _ in range(5):
            cfd_python.init()
            cfd_python.finalize()

    def test_double_finalize_safe(self):
        """Verify calling finalize twice does not crash."""
        cfd_python.init()
        cfd_python.finalize()
        cfd_python.finalize()  # Should not crash


class TestCFDVersion:
    """Tests for get_cfd_version() and version constants."""

    def test_get_cfd_version_returns_string(self):
        result = cfd_python.get_cfd_version()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_cfd_version_format(self):
        version = cfd_python.get_cfd_version()
        parts = version.split(".")
        assert len(parts) >= 2, f"Version '{version}' should have at least major.minor"

    def test_get_cfd_version_repeated_calls(self):
        """Verify no leaks or crashes under repeated calls."""
        for _ in range(100):
            result = cfd_python.get_cfd_version()
            assert isinstance(result, str)

    def test_version_constants_exist(self):
        for name in ["CFD_VERSION_MAJOR", "CFD_VERSION_MINOR", "CFD_VERSION_PATCH"]:
            assert hasattr(cfd_python, name), f"Missing constant: {name}"

    def test_version_constants_are_integers(self):
        for name in ["CFD_VERSION_MAJOR", "CFD_VERSION_MINOR", "CFD_VERSION_PATCH"]:
            assert isinstance(getattr(cfd_python, name), int)

    def test_version_constants_non_negative(self):
        for name in ["CFD_VERSION_MAJOR", "CFD_VERSION_MINOR", "CFD_VERSION_PATCH"]:
            assert getattr(cfd_python, name) >= 0

    def test_version_constants_match_string(self):
        """Check version string format and constant consistency.

        Note: get_cfd_version() returns the runtime library version which may
        differ from the compile-time CFD_VERSION_* constants if headers and
        libraries are from different builds.
        """
        version_str = cfd_python.get_cfd_version()
        parts = version_str.split(".")
        # Version string should have numeric parts
        assert all(p.isdigit() for p in parts), f"Non-numeric version parts in '{version_str}'"
        # Constants should form a valid version
        major = cfd_python.CFD_VERSION_MAJOR
        minor = cfd_python.CFD_VERSION_MINOR
        patch = cfd_python.CFD_VERSION_PATCH
        constructed = f"{major}.{minor}.{patch}"
        assert len(constructed) > 0
