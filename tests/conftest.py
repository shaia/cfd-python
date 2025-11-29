"""
Pytest configuration for CFD Python tests
"""
import pytest
import sys
import os

# Add the build directory to the path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Use pytest.importorskip for proper import handling - this will:
# - Skip tests with a clear message if module isn't built
# - Show as skipped (not passed) in test reports
# - Fail loudly in CI if the module should have been built
pytest.importorskip(
    "cfd_python",
    reason="CFD Python C extension not built. Run 'pip install -e .' first."
)
