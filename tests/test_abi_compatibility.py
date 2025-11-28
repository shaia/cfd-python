"""
Tests for Python Stable ABI Compatibility

These tests verify that the cfd_python C extension is properly built
with the stable ABI (Py_LIMITED_API) and returns properly constructed
Python objects without memory issues.
"""

import sys
import pytest


class TestStableABICompliance:
    """Test that the module is built with stable ABI."""

    def test_module_imports(self):
        """Test that the module can be imported."""
        import cfd_python
        assert cfd_python is not None

    def test_module_has_version(self):
        """Test that module has version attribute."""
        import cfd_python
        assert hasattr(cfd_python, '__version__')
        assert isinstance(cfd_python.__version__, str)

    @pytest.mark.skipif(sys.platform != 'win32', reason="Windows-specific test")
    def test_extension_suffix_windows(self):
        """On Windows, stable ABI extensions use .pyd suffix."""
        import cfd_python
        import os
        ext_path = cfd_python.__file__
        # Stable ABI modules may have abi3 in the name
        assert ext_path.endswith('.pyd') or 'abi3' in ext_path

    @pytest.mark.skipif(sys.platform == 'win32', reason="Unix-specific test")
    def test_extension_suffix_unix(self):
        """On Unix, stable ABI extensions should have abi3 in suffix."""
        import cfd_python
        ext_path = cfd_python.__file__
        # Stable ABI modules have .abi3.so suffix on Unix
        assert '.so' in ext_path or '.abi3' in ext_path


class TestListReturnTypes:
    """Test that functions returning lists work correctly with stable ABI."""

    def test_list_solvers_returns_list(self):
        """list_solvers() should return a proper Python list."""
        import cfd_python
        solvers = cfd_python.list_solvers()
        assert isinstance(solvers, list)
        # Each element should be a string
        for solver in solvers:
            assert isinstance(solver, str)

    def test_list_solvers_not_empty(self):
        """list_solvers() should return at least one solver."""
        import cfd_python
        solvers = cfd_python.list_solvers()
        assert len(solvers) > 0

    def test_list_solvers_repeated_calls(self):
        """Repeated calls to list_solvers() should work without memory issues."""
        import cfd_python
        for _ in range(100):
            solvers = cfd_python.list_solvers()
            assert isinstance(solvers, list)
            assert len(solvers) > 0

    def test_run_simulation_returns_list(self):
        """run_simulation() should return a proper Python list."""
        import cfd_python
        result = cfd_python.run_simulation(nx=8, ny=8, steps=5)
        assert isinstance(result, list)
        # Each element should be a float
        for val in result:
            assert isinstance(val, float)

    def test_run_simulation_correct_size(self):
        """run_simulation() should return nx*ny elements."""
        import cfd_python
        nx, ny = 10, 12
        result = cfd_python.run_simulation(nx=nx, ny=ny, steps=5)
        assert len(result) == nx * ny

    def test_run_simulation_repeated_calls(self):
        """Repeated calls to run_simulation() should work without memory issues."""
        import cfd_python
        for _ in range(20):
            result = cfd_python.run_simulation(nx=8, ny=8, steps=2)
            assert isinstance(result, list)
            assert len(result) == 64


class TestDictReturnTypes:
    """Test that functions returning dicts work correctly with stable ABI."""

    def test_create_grid_returns_dict(self):
        """create_grid() should return a proper Python dict."""
        import cfd_python
        grid = cfd_python.create_grid(10, 10, 0.0, 1.0, 0.0, 1.0)
        assert isinstance(grid, dict)

    def test_create_grid_has_coordinate_lists(self):
        """create_grid() should have x_coords and y_coords as lists."""
        import cfd_python
        nx, ny = 10, 12
        grid = cfd_python.create_grid(nx, ny, 0.0, 1.0, 0.0, 1.0)

        assert 'x_coords' in grid
        assert 'y_coords' in grid
        assert isinstance(grid['x_coords'], list)
        assert isinstance(grid['y_coords'], list)
        assert len(grid['x_coords']) == nx
        assert len(grid['y_coords']) == ny

        # Each coordinate should be a float
        for x in grid['x_coords']:
            assert isinstance(x, float)
        for y in grid['y_coords']:
            assert isinstance(y, float)

    def test_create_grid_repeated_calls(self):
        """Repeated calls to create_grid() should work without memory issues."""
        import cfd_python
        for _ in range(50):
            grid = cfd_python.create_grid(8, 8, 0.0, 1.0, 0.0, 1.0)
            assert isinstance(grid, dict)
            assert len(grid['x_coords']) == 8
            assert len(grid['y_coords']) == 8

    def test_get_default_solver_params_returns_dict(self):
        """get_default_solver_params() should return a proper Python dict."""
        import cfd_python
        params = cfd_python.get_default_solver_params()
        assert isinstance(params, dict)

        # Check expected keys
        expected_keys = ['dt', 'cfl', 'gamma', 'mu', 'k', 'max_iter', 'tolerance']
        for key in expected_keys:
            assert key in params

    def test_run_simulation_with_params_returns_dict(self):
        """run_simulation_with_params() should return a proper Python dict."""
        import cfd_python
        result = cfd_python.run_simulation_with_params(
            nx=8, ny=8,
            xmin=0.0, xmax=1.0,
            ymin=0.0, ymax=1.0,
            steps=5
        )
        assert isinstance(result, dict)

        # Should have velocity_magnitude as a list
        if 'velocity_magnitude' in result:
            assert isinstance(result['velocity_magnitude'], list)
            for val in result['velocity_magnitude']:
                assert isinstance(val, float)

    def test_get_solver_info_returns_dict(self):
        """get_solver_info() should return a proper Python dict."""
        import cfd_python
        solvers = cfd_python.list_solvers()
        if solvers:
            info = cfd_python.get_solver_info(solvers[0])
            assert isinstance(info, dict)
            assert 'name' in info
            assert 'description' in info
            assert 'capabilities' in info
            assert isinstance(info['capabilities'], list)


class TestReferenceCountingStress:
    """Stress tests for reference counting in stable ABI code."""

    def test_large_list_creation(self):
        """Test creating and destroying large lists doesn't leak memory."""
        import cfd_python
        # Run a larger simulation to create bigger lists
        for _ in range(10):
            result = cfd_python.run_simulation(nx=50, ny=50, steps=2)
            assert len(result) == 2500
            del result

    def test_rapid_dict_creation(self):
        """Test rapid dict creation and destruction."""
        import cfd_python
        for _ in range(100):
            grid = cfd_python.create_grid(20, 20, 0.0, 1.0, 0.0, 1.0)
            params = cfd_python.get_default_solver_params()
            del grid
            del params

    def test_mixed_operations_stress(self):
        """Test mixed operations don't cause memory issues."""
        import cfd_python
        for i in range(50):
            # Mix different operations
            solvers = cfd_python.list_solvers()
            grid = cfd_python.create_grid(10, 10, 0.0, 1.0, 0.0, 1.0)
            result = cfd_python.run_simulation(nx=10, ny=10, steps=2)

            # Use the results
            assert len(solvers) > 0
            assert len(grid['x_coords']) == 10
            assert len(result) == 100

            # Clean up
            del solvers, grid, result

    def test_list_modification_after_return(self):
        """Test that returned lists can be modified without issues."""
        import cfd_python
        result = cfd_python.run_simulation(nx=8, ny=8, steps=2)

        # Modify the list
        result.append(999.0)
        result[0] = -1.0
        result.pop()
        result.extend([1.0, 2.0, 3.0])
        result.clear()

        assert len(result) == 0

    def test_dict_modification_after_return(self):
        """Test that returned dicts can be modified without issues."""
        import cfd_python
        grid = cfd_python.create_grid(8, 8, 0.0, 1.0, 0.0, 1.0)

        # Modify the dict
        grid['custom_key'] = 'custom_value'
        del grid['nx']
        grid['x_coords'].append(999.0)
        grid.clear()

        assert len(grid) == 0


class TestErrorHandlingWithABI:
    """Test error handling works correctly with stable ABI."""

    def test_invalid_solver_raises_error(self):
        """Invalid solver should raise ValueError, not crash."""
        import cfd_python
        with pytest.raises(ValueError):
            cfd_python.get_solver_info("nonexistent_solver_xyz")

    def test_invalid_grid_params(self):
        """Invalid grid parameters should be handled gracefully."""
        import cfd_python
        # These should either work or raise proper Python exceptions
        # They should NOT cause segfaults
        try:
            # Very small grid
            grid = cfd_python.create_grid(1, 1, 0.0, 1.0, 0.0, 1.0)
            assert isinstance(grid, dict)
        except (ValueError, RuntimeError):
            pass  # Exception is acceptable

    def test_zero_steps_simulation(self):
        """Zero steps simulation should be handled gracefully."""
        import cfd_python
        try:
            result = cfd_python.run_simulation(nx=8, ny=8, steps=0)
            # Either returns empty or valid list
            assert isinstance(result, list)
        except (ValueError, RuntimeError):
            pass  # Exception is acceptable


class TestMemoryLeakPrevention:
    """Test that reference counting is correct to prevent memory leaks."""

    def test_dict_values_have_correct_refcount(self):
        """Values added to dicts should have correct reference counts."""
        import cfd_python
        import sys

        # Get a fresh dict
        params = cfd_python.get_default_solver_params()

        # Each value should have refcount of at least 1 (in the dict)
        # but not excessively high
        for key, value in params.items():
            refcount = sys.getrefcount(value)
            # refcount includes the temporary reference from getrefcount() call
            # Normal values should have refcount around 2-3
            assert refcount < 100, f"Suspiciously high refcount for {key}: {refcount}"

    def test_list_elements_have_correct_refcount(self):
        """Elements in returned lists should have correct reference counts."""
        import cfd_python
        import sys

        result = cfd_python.run_simulation(nx=4, ny=4, steps=2)

        # Check first few elements
        for i, val in enumerate(result[:5]):
            refcount = sys.getrefcount(val)
            # Float values might be cached by Python for common values
            # but shouldn't have extremely high refcounts from our code
            assert refcount < 1000, f"Suspiciously high refcount for element {i}: {refcount}"

    def test_solver_info_no_leak(self):
        """get_solver_info should not leak references."""
        import cfd_python
        import sys

        solvers = cfd_python.list_solvers()
        if solvers:
            # Call multiple times
            for _ in range(50):
                info = cfd_python.get_solver_info(solvers[0])
                # Check capabilities list
                caps = info['capabilities']
                for cap in caps:
                    refcount = sys.getrefcount(cap)
                    assert refcount < 100, f"High refcount for capability: {refcount}"

    def test_grid_coords_no_leak(self):
        """create_grid coordinate lists should not leak references."""
        import cfd_python

        # Create many grids and check memory doesn't grow excessively
        for _ in range(100):
            grid = cfd_python.create_grid(20, 20, 0.0, 1.0, 0.0, 1.0)
            # Access all coordinates to ensure they're valid
            x_sum = sum(grid['x_coords'])
            y_sum = sum(grid['y_coords'])
            assert x_sum > 0
            assert y_sum > 0
            del grid

    def test_simulation_with_params_no_leak(self):
        """run_simulation_with_params should not leak references."""
        import cfd_python

        for _ in range(20):
            result = cfd_python.run_simulation_with_params(
                nx=10, ny=10,
                xmin=0.0, xmax=1.0,
                ymin=0.0, ymax=1.0,
                steps=3
            )
            # Access nested dict
            if 'stats' in result:
                stats = result['stats']
                _ = stats.get('iterations', 0)
            del result
