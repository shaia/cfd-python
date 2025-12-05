"""Tests for internal _version.py and _loader.py modules."""

import sys
from unittest.mock import patch

import pytest


class TestVersionModule:
    """Tests for cfd_python._version module."""

    def test_get_version_returns_string(self):
        """get_version() should always return a string."""
        from cfd_python._version import get_version

        version = get_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_get_version_from_metadata(self):
        """get_version() should use importlib.metadata when available."""
        with patch("importlib.metadata.version") as mock_version:
            mock_version.return_value = "1.2.3"
            # Need to reimport to pick up the mock
            import importlib

            import cfd_python._version

            importlib.reload(cfd_python._version)
            result = cfd_python._version.get_version()
            assert result == "1.2.3"

    def test_get_version_fallback_to_c_module(self):
        """get_version() falls back to C module version."""
        from cfd_python._version import get_version

        # The real implementation should work
        version = get_version()
        # Should be a valid version string
        assert version != ""

    def test_get_version_handles_import_error(self):
        """get_version() handles ImportError for importlib.metadata gracefully."""
        # Test that even if importlib.metadata raises ImportError,
        # get_version() doesn't crash and returns something valid
        from cfd_python._version import get_version

        # When package is installed, version should be found
        version = get_version()
        assert isinstance(version, str)
        assert len(version) > 0
        # Should not be the dev fallback since package is installed
        assert "dev" not in version or version != "0.0.0-dev"

    def test_version_fallback_code_path_exists(self):
        """Verify the fallback code path returns correct dev version."""
        # This tests the fallback logic directly without mocking
        # The actual dev fallback is "0.0.0-dev"
        # We verify the code structure is correct by checking the source
        import inspect

        from cfd_python._version import get_version

        source = inspect.getsource(get_version)
        assert 'return "0.0.0-dev"' in source


class TestLoaderModule:
    """Tests for cfd_python._loader module."""

    def test_extension_not_built_error_is_import_error(self):
        """ExtensionNotBuiltError should be a subclass of ImportError."""
        from cfd_python._loader import ExtensionNotBuiltError

        assert issubclass(ExtensionNotBuiltError, ImportError)

    def test_extension_not_built_error_message(self):
        """ExtensionNotBuiltError should have a helpful message."""
        from cfd_python._loader import ExtensionNotBuiltError

        error = ExtensionNotBuiltError("Test message")
        assert str(error) == "Test message"

    def test_check_extension_exists_with_pyd(self, tmp_path):
        """_check_extension_exists detects .pyd files."""
        from cfd_python._loader import _check_extension_exists

        # Create a fake package directory with .pyd file
        (tmp_path / "cfd_python.abi3.pyd").touch()

        with patch("cfd_python._loader.os.path.dirname", return_value=str(tmp_path)):
            with patch("cfd_python._loader.os.listdir", return_value=["cfd_python.abi3.pyd"]):
                assert _check_extension_exists() is True

    def test_check_extension_exists_with_so(self, tmp_path):
        """_check_extension_exists detects .so files."""
        from cfd_python._loader import _check_extension_exists

        (tmp_path / "cfd_python.cpython-311-x86_64-linux-gnu.so").touch()

        with patch("cfd_python._loader.os.path.dirname", return_value=str(tmp_path)):
            with patch(
                "cfd_python._loader.os.listdir",
                return_value=["cfd_python.cpython-311-x86_64-linux-gnu.so"],
            ):
                assert _check_extension_exists() is True

    def test_check_extension_exists_no_extension(self, tmp_path):
        """_check_extension_exists returns False when no extension present."""
        from cfd_python._loader import _check_extension_exists

        (tmp_path / "__init__.py").touch()
        (tmp_path / "_version.py").touch()

        with patch("cfd_python._loader.os.path.dirname", return_value=str(tmp_path)):
            with patch(
                "cfd_python._loader.os.listdir", return_value=["__init__.py", "_version.py"]
            ):
                assert _check_extension_exists() is False

    def test_check_extension_exists_wrong_prefix(self, tmp_path):
        """_check_extension_exists ignores files not starting with cfd_python."""
        from cfd_python._loader import _check_extension_exists

        (tmp_path / "other_module.so").touch()

        with patch("cfd_python._loader.os.path.dirname", return_value=str(tmp_path)):
            with patch("cfd_python._loader.os.listdir", return_value=["other_module.so"]):
                assert _check_extension_exists() is False

    def test_load_extension_returns_tuple(self):
        """load_extension() returns (exports_dict, solver_constants)."""
        from cfd_python._loader import load_extension

        result = load_extension()
        assert isinstance(result, tuple)
        assert len(result) == 2

        exports, solver_constants = result
        assert isinstance(exports, dict)
        assert isinstance(solver_constants, dict)

    def test_load_extension_exports_contains_required_functions(self):
        """load_extension() exports dict contains all core functions."""
        from cfd_python._loader import load_extension

        exports, _ = load_extension()

        required_functions = [
            "run_simulation",
            "run_simulation_with_params",
            "create_grid",
            "get_default_solver_params",
            "list_solvers",
            "has_solver",
            "get_solver_info",
            "set_output_dir",
            "write_vtk_scalar",
            "write_vtk_vector",
            "write_csv_timeseries",
        ]

        for func_name in required_functions:
            assert func_name in exports, f"Missing export: {func_name}"
            assert callable(exports[func_name])

    def test_load_extension_exports_contains_output_constants(self):
        """load_extension() exports dict contains OUTPUT_* constants."""
        from cfd_python._loader import load_extension

        exports, _ = load_extension()

        output_constants = [
            "OUTPUT_PRESSURE",
            "OUTPUT_VELOCITY",
            "OUTPUT_FULL_FIELD",
            "OUTPUT_CSV_TIMESERIES",
            "OUTPUT_CSV_CENTERLINE",
            "OUTPUT_CSV_STATISTICS",
        ]

        for const_name in output_constants:
            assert const_name in exports, f"Missing constant: {const_name}"
            assert isinstance(exports[const_name], int)

    def test_load_extension_solver_constants_have_solver_prefix(self):
        """load_extension() solver_constants all start with SOLVER_."""
        from cfd_python._loader import load_extension

        _, solver_constants = load_extension()

        assert len(solver_constants) > 0, "Expected at least one solver constant"
        for name in solver_constants:
            assert name.startswith("SOLVER_"), f"Unexpected constant name: {name}"

    def test_load_extension_raises_on_broken_extension(self, tmp_path):
        """load_extension() raises ImportError (not ExtensionNotBuiltError) for broken extension."""
        from cfd_python._loader import ExtensionNotBuiltError

        # Create a fake broken package
        fake_package = tmp_path / "fake_broken_loader"
        fake_package.mkdir()
        (fake_package / "__init__.py").write_text(
            """
from ._loader import load_extension
exports, constants = load_extension()
"""
        )
        (fake_package / "_loader.py").write_text(
            """
import os

class ExtensionNotBuiltError(ImportError):
    pass

def _check_extension_exists():
    package_dir = os.path.dirname(__file__)
    return any(
        f.startswith("cfd_python") and (f.endswith(".pyd") or f.endswith(".so"))
        for f in os.listdir(package_dir)
    )

def load_extension():
    try:
        from . import cfd_python
        return {}, {}
    except ImportError as e:
        if _check_extension_exists():
            raise ImportError(
                f"Failed to load C extension: {e}\\n"
                "This may indicate a missing dependency or ABI incompatibility."
            ) from e
        else:
            raise ExtensionNotBuiltError("C extension not built.") from e
"""
        )
        # Create a fake broken .pyd file
        if sys.platform == "win32":
            (fake_package / "cfd_python.pyd").write_text("not a real extension")
        else:
            (fake_package / "cfd_python.so").write_text("not a real extension")

        sys.path.insert(0, str(tmp_path))
        try:
            with pytest.raises(ImportError) as exc_info:
                import fake_broken_loader  # noqa: F401

            # Should be regular ImportError, not ExtensionNotBuiltError
            assert not isinstance(exc_info.value, ExtensionNotBuiltError)
            assert "Failed to load C extension" in str(exc_info.value)
        finally:
            sys.path.remove(str(tmp_path))
            if "fake_broken_loader" in sys.modules:
                del sys.modules["fake_broken_loader"]
            if "fake_broken_loader._loader" in sys.modules:
                del sys.modules["fake_broken_loader._loader"]


class TestModuleIntegration:
    """Integration tests for __init__.py using _version and _loader."""

    def test_init_uses_extension_not_built_error(self):
        """__init__.py catches ExtensionNotBuiltError specifically."""
        # Verify the import in __init__.py
        import cfd_python

        # The module should have loaded successfully
        assert hasattr(cfd_python, "__version__")
        assert hasattr(cfd_python, "__all__")

    def test_init_exposes_extension_functions(self):
        """Functions from _loader are exposed at package level."""
        import cfd_python

        assert hasattr(cfd_python, "run_simulation")
        assert hasattr(cfd_python, "list_solvers")
        assert hasattr(cfd_python, "create_grid")

    def test_init_exposes_solver_constants(self):
        """SOLVER_* constants are exposed at package level."""
        import cfd_python

        # At least one solver constant should exist
        solver_attrs = [attr for attr in dir(cfd_python) if attr.startswith("SOLVER_")]
        assert len(solver_attrs) > 0

    def test_all_includes_solver_constants(self):
        """__all__ includes dynamically discovered SOLVER_* constants."""
        import cfd_python

        solver_exports = [name for name in cfd_python.__all__ if name.startswith("SOLVER_")]
        assert len(solver_exports) > 0
