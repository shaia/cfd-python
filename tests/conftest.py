"""
Pytest configuration for CFD Python tests
"""
import pytest
import sys
import os

# Add the build directory to the path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Check each required module separately for clearer error messages
def _check_module_import(module_name, error_message):
    """Check if a module can be imported and provide specific error message."""
    try:
        __import__(module_name)
        return True
    except ImportError as e:
        pytest.skip(f"{error_message} (ImportError: {e})")
        return False

# Verify cfd_python C extension is available and functional
try:
    import cfd_python
    # Check if extension actually loaded (not just dev mode stub)
    if not hasattr(cfd_python, 'list_solvers'):
        # In CI (indicated by CI env var), fail instead of skip
        if os.environ.get('CI'):
            raise RuntimeError(
                "CFD Python C extension not built. "
                "The wheel may be missing the compiled extension."
            )
        else:
            pytest.skip(
                "CFD Python C extension not built (development mode). "
                "Run 'pip install -e .' to build the extension.",
                allow_module_level=True
            )
except ImportError as e:
    error_str = str(e)
    if "DLL load failed" in error_str or "cannot open shared object" in error_str:
        reason = f"CFD Python C extension failed to load (missing dependencies): {e}"
    elif "No module named" in error_str:
        reason = "CFD Python C extension not built. Run 'pip install -e .' first."
    else:
        reason = f"CFD Python import failed: {e}"
    # In CI, fail instead of skip for ImportError
    if os.environ.get('CI'):
        raise RuntimeError(reason) from e
    pytest.skip(reason, allow_module_level=True)
