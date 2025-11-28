"""
Pytest configuration and shared fixtures for cfd_python tests.
"""

import pytest
import sys


def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "stress: marks tests as stress tests"
    )


@pytest.fixture
def cfd_module():
    """Fixture that provides the cfd_python module."""
    import cfd_python
    return cfd_python


@pytest.fixture
def small_grid_params():
    """Fixture for small grid parameters."""
    return {
        'nx': 8,
        'ny': 8,
        'xmin': 0.0,
        'xmax': 1.0,
        'ymin': 0.0,
        'ymax': 1.0,
    }


@pytest.fixture
def medium_grid_params():
    """Fixture for medium grid parameters."""
    return {
        'nx': 32,
        'ny': 32,
        'xmin': 0.0,
        'xmax': 1.0,
        'ymin': 0.0,
        'ymax': 1.0,
    }
