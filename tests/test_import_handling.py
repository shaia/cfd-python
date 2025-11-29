"""
Tests for import error handling in cfd_python/__init__.py

These tests verify the behavior when:
1. Extension exists but fails to load (broken installation)
2. No extension exists (development mode)
"""
import os
import sys
import tempfile
import shutil
import pytest


class TestImportErrorHandling:
    """Test import error handling logic"""

    def test_broken_extension_raises_import_error(self, tmp_path):
        """Test that a broken extension file raises ImportError with helpful message"""
        # Create a fake package directory with a broken extension
        # Use a unique name to avoid conflicts with real cfd_python
        fake_package = tmp_path / "fake_cfd_broken"
        fake_package.mkdir()

        # Create __init__.py with the same logic as the real one
        # but importing from fake_cfd_broken submodule
        init_content = '''
import os as _os

_CORE_EXPORTS = ["run_simulation", "list_solvers"]
__version__ = None

try:
    from .fake_cfd_broken import run_simulation, list_solvers
except ImportError as e:
    _package_dir = _os.path.dirname(__file__)
    _extension_exists = any(
        f.startswith('fake_cfd_broken') and (f.endswith('.pyd') or f.endswith('.so'))
        for f in _os.listdir(_package_dir)
    )
    if _extension_exists:
        raise ImportError(
            f"Failed to load C extension: {e}\\n"
            "The extension file exists but could not be imported. "
            "This may indicate a missing dependency or ABI incompatibility."
        ) from e
    else:
        __all__ = _CORE_EXPORTS
        if __version__ is None:
            __version__ = "0.0.0-dev"
'''
        (fake_package / "__init__.py").write_text(init_content)

        # Create a fake broken extension file
        if sys.platform == "win32":
            (fake_package / "fake_cfd_broken.pyd").write_text("not a real extension")
        else:
            (fake_package / "fake_cfd_broken.so").write_text("not a real extension")

        # Add to path and try to import
        sys.path.insert(0, str(tmp_path))
        try:
            with pytest.raises(ImportError) as exc_info:
                import fake_cfd_broken

            # Verify the error message is helpful
            assert "Failed to load C extension" in str(exc_info.value)
            assert "missing dependency or ABI incompatibility" in str(exc_info.value)
        finally:
            sys.path.remove(str(tmp_path))
            # Clean up module cache
            if "fake_cfd_broken" in sys.modules:
                del sys.modules["fake_cfd_broken"]

    def test_dev_mode_no_extension(self, tmp_path):
        """Test that missing extension falls back to dev mode gracefully"""
        # Create a fake package directory without extension
        fake_package = tmp_path / "fake_cfd_dev"
        fake_package.mkdir()

        # Create __init__.py with the same logic
        init_content = '''
import os as _os

_CORE_EXPORTS = ["run_simulation", "list_solvers"]
__version__ = None
__all__ = []

try:
    from .cfd_python import run_simulation, list_solvers
    __all__ = _CORE_EXPORTS
except ImportError as e:
    _package_dir = _os.path.dirname(__file__)
    _extension_exists = any(
        f.startswith('cfd_python') and (f.endswith('.pyd') or f.endswith('.so'))
        for f in _os.listdir(_package_dir)
    )
    if _extension_exists:
        raise ImportError(
            f"Failed to load cfd_python C extension: {e}\\n"
            "The extension file exists but could not be imported. "
            "This may indicate a missing dependency or ABI incompatibility."
        ) from e
    else:
        __all__ = _CORE_EXPORTS
        if __version__ is None:
            __version__ = "0.0.0-dev"
'''
        (fake_package / "__init__.py").write_text(init_content)

        # Add to path and import
        sys.path.insert(0, str(tmp_path))
        try:
            import fake_cfd_dev

            # Should have dev version
            assert fake_cfd_dev.__version__ == "0.0.0-dev"
            # Should have __all__ set
            assert fake_cfd_dev.__all__ == ["run_simulation", "list_solvers"]
        finally:
            sys.path.remove(str(tmp_path))
            if "fake_cfd_dev" in sys.modules:
                del sys.modules["fake_cfd_dev"]

    def test_real_module_loads_successfully(self):
        """Test that the real cfd_python module loads without error"""
        # This verifies the actual installed module works
        import cfd_python

        # Should have version
        assert hasattr(cfd_python, '__version__')
        assert cfd_python.__version__ is not None

        # Should have core functions
        assert hasattr(cfd_python, 'list_solvers')
        assert callable(cfd_python.list_solvers)

        # list_solvers should return a non-empty list
        solvers = cfd_python.list_solvers()
        assert isinstance(solvers, list)
        assert len(solvers) > 0

    def test_extension_detection_logic(self, tmp_path):
        """Test that extension detection correctly identifies .pyd and .so files"""
        test_dir = tmp_path / "test_detection"
        test_dir.mkdir()

        # Test with no extension files
        files = list(test_dir.iterdir())
        has_extension = any(
            f.name.startswith('cfd_python') and (f.name.endswith('.pyd') or f.name.endswith('.so'))
            for f in files
        )
        assert not has_extension

        # Test with .pyd file
        (test_dir / "cfd_python.cp311-win_amd64.pyd").touch()
        files = list(test_dir.iterdir())
        has_extension = any(
            f.name.startswith('cfd_python') and (f.name.endswith('.pyd') or f.name.endswith('.so'))
            for f in files
        )
        assert has_extension

        # Clean and test with .so file
        (test_dir / "cfd_python.cp311-win_amd64.pyd").unlink()
        (test_dir / "cfd_python.cpython-311-x86_64-linux-gnu.so").touch()
        files = list(test_dir.iterdir())
        has_extension = any(
            f.name.startswith('cfd_python') and (f.name.endswith('.pyd') or f.name.endswith('.so'))
            for f in files
        )
        assert has_extension

        # Test with unrelated .so file (should not match)
        (test_dir / "cfd_python.cpython-311-x86_64-linux-gnu.so").unlink()
        (test_dir / "other_module.so").touch()
        files = list(test_dir.iterdir())
        has_extension = any(
            f.name.startswith('cfd_python') and (f.name.endswith('.pyd') or f.name.endswith('.so'))
            for f in files
        )
        assert not has_extension
