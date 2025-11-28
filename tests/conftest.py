"""
Pytest configuration and shared fixtures for CFD Python tests
"""
import pytest
import sys
import os

# Add the build directory to the path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    import cfd_python
except ImportError:
    pytest.skip("CFD Python module not built yet", allow_module_level=True)


@pytest.fixture
def cfd():
    """Provide the cfd_python module"""
    return cfd_python


@pytest.fixture
def small_grid_params():
    """Small grid parameters for quick tests"""
    return {
        'nx': 5,
        'ny': 5,
        'xmin': 0.0,
        'xmax': 1.0,
        'ymin': 0.0,
        'ymax': 1.0,
    }


@pytest.fixture
def default_solver_params(cfd):
    """Default solver parameters"""
    return cfd.get_default_solver_params()
