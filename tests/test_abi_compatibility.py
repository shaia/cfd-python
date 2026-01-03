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

        assert hasattr(cfd_python, "__version__")
        assert isinstance(cfd_python.__version__, str)

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
    def test_extension_suffix_windows(self):
        """On Windows, extensions use .pyd suffix or are Python packages."""

        import cfd_python

        ext_path = cfd_python.__file__
        # Can be a .pyd extension, abi3 extension, or Python package __init__.py
        assert ext_path.endswith(".pyd") or "abi3" in ext_path or ext_path.endswith("__init__.py")

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix-specific test")
    def test_extension_suffix_unix(self):
        """On Unix, extensions should have .so suffix or be Python packages."""
        import cfd_python

        ext_path = cfd_python.__file__
        # Can be .so extension, abi3 extension, or Python package __init__.py
        assert ".so" in ext_path or ".abi3" in ext_path or ext_path.endswith("__init__.py")


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

        assert "x_coords" in grid
        assert "y_coords" in grid
        assert isinstance(grid["x_coords"], list)
        assert isinstance(grid["y_coords"], list)
        assert len(grid["x_coords"]) == nx
        assert len(grid["y_coords"]) == ny

        # Each coordinate should be a float
        for x in grid["x_coords"]:
            assert isinstance(x, float)
        for y in grid["y_coords"]:
            assert isinstance(y, float)

    def test_create_grid_repeated_calls(self):
        """Repeated calls to create_grid() should work without memory issues."""
        import cfd_python

        for _ in range(50):
            grid = cfd_python.create_grid(8, 8, 0.0, 1.0, 0.0, 1.0)
            assert isinstance(grid, dict)
            assert len(grid["x_coords"]) == 8
            assert len(grid["y_coords"]) == 8

    def test_get_default_solver_params_returns_dict(self):
        """get_default_solver_params() should return a proper Python dict."""
        import cfd_python

        params = cfd_python.get_default_solver_params()
        assert isinstance(params, dict)

        # Check expected keys
        expected_keys = ["dt", "cfl", "gamma", "mu", "k", "max_iter", "tolerance"]
        for key in expected_keys:
            assert key in params

    def test_run_simulation_with_params_returns_dict(self):
        """run_simulation_with_params() should return a proper Python dict."""
        import cfd_python

        result = cfd_python.run_simulation_with_params(
            nx=8, ny=8, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0, steps=5
        )
        assert isinstance(result, dict)

        # Should have velocity_magnitude as a list
        if "velocity_magnitude" in result:
            assert isinstance(result["velocity_magnitude"], list)
            for val in result["velocity_magnitude"]:
                assert isinstance(val, float)

    def test_get_solver_info_returns_dict(self):
        """get_solver_info() should return a proper Python dict."""
        import cfd_python

        solvers = cfd_python.list_solvers()
        if solvers:
            info = cfd_python.get_solver_info(solvers[0])
            assert isinstance(info, dict)
            assert "name" in info
            assert "description" in info
            assert "capabilities" in info
            assert isinstance(info["capabilities"], list)


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
            assert len(grid["x_coords"]) == 10
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
        grid["custom_key"] = "custom_value"
        del grid["nx"]
        grid["x_coords"].append(999.0)
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
        import sys

        import cfd_python

        # Get a fresh dict
        params = cfd_python.get_default_solver_params()

        # Each value should have refcount of at least 1 (in the dict)
        # Note: Python caches/interns small integers and some common values,
        # which can have very high refcounts (millions) - this is normal.
        # We only check that float values (which aren't cached) have reasonable refcounts.
        for key, value in params.items():
            if isinstance(value, float):
                refcount = sys.getrefcount(value)
                # refcount includes the temporary reference from getrefcount() call
                # Float values should have refcount around 2-3 unless they're 0.0 or 1.0
                if value not in (0.0, 1.0, -1.0):
                    assert refcount < 100, f"Suspiciously high refcount for {key}: {refcount}"

    def test_list_elements_have_correct_refcount(self):
        """Elements in returned lists should have correct reference counts."""
        import sys

        import cfd_python

        result = cfd_python.run_simulation(nx=4, ny=4, steps=2)

        # Check first few elements
        for i, val in enumerate(result[:5]):
            refcount = sys.getrefcount(val)
            # Float values might be cached by Python for common values
            # but shouldn't have extremely high refcounts from our code
            assert refcount < 1000, f"Suspiciously high refcount for element {i}: {refcount}"

    def test_solver_info_no_leak(self):
        """get_solver_info should not leak references."""
        import sys

        import cfd_python

        solvers = cfd_python.list_solvers()
        if solvers:
            # Call multiple times
            for _ in range(50):
                info = cfd_python.get_solver_info(solvers[0])
                # Check capabilities list
                caps = info["capabilities"]
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
            x_sum = sum(grid["x_coords"])
            y_sum = sum(grid["y_coords"])
            assert x_sum > 0
            assert y_sum > 0
            del grid

    def test_simulation_with_params_no_leak(self):
        """run_simulation_with_params should not leak references."""
        import cfd_python

        for _ in range(20):
            result = cfd_python.run_simulation_with_params(
                nx=10, ny=10, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0, steps=3
            )
            # Verify result structure to ensure it's properly formed
            assert "velocity_magnitude" in result
            assert len(result["velocity_magnitude"]) == 100
            # Access nested dict if present
            if "stats" in result:
                assert isinstance(result["stats"], dict)
            del result


class TestPyLongAndPyUnicodeReturns:
    """Test that functions returning PyLong and PyUnicode handle NULL correctly.

    These tests cover the NULL handling fixes for PyLong_FromLong and
    PyUnicode_FromString return values in functions like get_last_status,
    get_simd_arch, get_last_error, etc.
    """

    def test_get_last_status_returns_int(self):
        """get_last_status() should return a proper Python int."""
        import cfd_python

        status = cfd_python.get_last_status()
        assert isinstance(status, int)

    def test_get_last_status_repeated_calls(self):
        """Repeated calls to get_last_status() should work without issues."""
        import cfd_python

        for _ in range(100):
            status = cfd_python.get_last_status()
            assert isinstance(status, int)
            # Status can be positive (success) or negative (error codes)

    def test_get_last_error_returns_string_or_none(self):
        """get_last_error() should return a string or None."""
        import cfd_python

        error = cfd_python.get_last_error()
        assert error is None or isinstance(error, str)

    def test_get_last_error_repeated_calls(self):
        """Repeated calls to get_last_error() should work without issues."""
        import cfd_python

        for _ in range(100):
            error = cfd_python.get_last_error()
            assert error is None or isinstance(error, str)

    def test_get_error_string_returns_string(self):
        """get_error_string() should return a proper Python string."""
        import cfd_python

        # Test with known status codes
        for status in [0, 1, 2, 3, 4, 5]:
            error_str = cfd_python.get_error_string(status)
            assert isinstance(error_str, str)
            assert len(error_str) > 0

    def test_get_error_string_repeated_calls(self):
        """Repeated calls to get_error_string() should work without issues."""
        import cfd_python

        for _ in range(100):
            error_str = cfd_python.get_error_string(0)
            assert isinstance(error_str, str)

    def test_bc_get_backend_returns_int(self):
        """bc_get_backend() should return a proper Python int."""
        import cfd_python

        backend = cfd_python.bc_get_backend()
        assert isinstance(backend, int)

    def test_bc_get_backend_repeated_calls(self):
        """Repeated calls to bc_get_backend() should work without issues."""
        import cfd_python

        for _ in range(100):
            backend = cfd_python.bc_get_backend()
            assert isinstance(backend, int)

    def test_bc_get_backend_name_returns_string(self):
        """bc_get_backend_name() should return a proper Python string."""
        import cfd_python

        name = cfd_python.bc_get_backend_name()
        assert isinstance(name, str)
        assert len(name) > 0

    def test_bc_get_backend_name_repeated_calls(self):
        """Repeated calls to bc_get_backend_name() should work without issues."""
        import cfd_python

        for _ in range(100):
            name = cfd_python.bc_get_backend_name()
            assert isinstance(name, str)
            assert len(name) > 0

    def test_backend_get_name_returns_string(self):
        """backend_get_name() should return a proper Python string."""
        import cfd_python

        # Get current backend first
        backend = cfd_python.bc_get_backend()
        name = cfd_python.backend_get_name(backend)
        assert isinstance(name, str)
        assert len(name) > 0

    def test_backend_get_name_repeated_calls(self):
        """Repeated calls to backend_get_name() should work without issues."""
        import cfd_python

        backend = cfd_python.bc_get_backend()
        for _ in range(100):
            name = cfd_python.backend_get_name(backend)
            assert isinstance(name, str)

    def test_get_simd_arch_returns_int(self):
        """get_simd_arch() should return a proper Python int."""
        import cfd_python

        arch = cfd_python.get_simd_arch()
        assert isinstance(arch, int)
        # Should be a valid SIMD constant
        valid_values = [cfd_python.SIMD_NONE, cfd_python.SIMD_AVX2, cfd_python.SIMD_NEON]
        assert arch in valid_values

    def test_get_simd_arch_repeated_calls(self):
        """Repeated calls to get_simd_arch() should work without issues."""
        import cfd_python

        for _ in range(100):
            arch = cfd_python.get_simd_arch()
            assert isinstance(arch, int)

    def test_get_simd_name_returns_string(self):
        """get_simd_name() should return a proper Python string."""
        import cfd_python

        name = cfd_python.get_simd_name()
        assert isinstance(name, str)
        valid_names = ["none", "avx2", "neon"]
        assert name in valid_names

    def test_get_simd_name_repeated_calls(self):
        """Repeated calls to get_simd_name() should work without issues."""
        import cfd_python

        for _ in range(100):
            name = cfd_python.get_simd_name()
            assert isinstance(name, str)


class TestPyLongPyUnicodeStress:
    """Stress tests for PyLong and PyUnicode return value handling."""

    def test_mixed_pylong_functions_stress(self):
        """Test rapid mixed calls to PyLong-returning functions."""
        import cfd_python

        for _ in range(50):
            status = cfd_python.get_last_status()
            backend = cfd_python.bc_get_backend()
            arch = cfd_python.get_simd_arch()

            assert isinstance(status, int)
            assert isinstance(backend, int)
            assert isinstance(arch, int)

            del status, backend, arch

    def test_mixed_pyunicode_functions_stress(self):
        """Test rapid mixed calls to PyUnicode-returning functions."""
        import cfd_python

        backend = cfd_python.bc_get_backend()
        for _ in range(50):
            error = cfd_python.get_last_error()
            error_str = cfd_python.get_error_string(0)
            backend_name = cfd_python.bc_get_backend_name()
            backend_name2 = cfd_python.backend_get_name(backend)
            simd_name = cfd_python.get_simd_name()

            assert error is None or isinstance(error, str)
            assert isinstance(error_str, str)
            assert isinstance(backend_name, str)
            assert isinstance(backend_name2, str)
            assert isinstance(simd_name, str)

            del error, error_str, backend_name, backend_name2, simd_name

    def test_all_fixed_functions_combined_stress(self):
        """Stress test all functions that had NULL handling fixes."""
        import cfd_python

        backend = cfd_python.bc_get_backend()

        for i in range(100):
            # PyLong returns
            status = cfd_python.get_last_status()
            bc_backend = cfd_python.bc_get_backend()
            arch = cfd_python.get_simd_arch()

            # PyUnicode returns
            error = cfd_python.get_last_error()
            error_str = cfd_python.get_error_string(status)
            bc_name = cfd_python.bc_get_backend_name()
            backend_name = cfd_python.backend_get_name(backend)
            simd_name = cfd_python.get_simd_name()

            # Verify all types
            assert isinstance(status, int)
            assert isinstance(bc_backend, int)
            assert isinstance(arch, int)
            assert error is None or isinstance(error, str)
            assert isinstance(error_str, str)
            assert isinstance(bc_name, str)
            assert isinstance(backend_name, str)
            assert isinstance(simd_name, str)

    def test_refcount_for_returned_strings(self):
        """Test that returned strings have correct reference counts."""
        import sys

        import cfd_python

        backend = cfd_python.bc_get_backend()

        # Get fresh strings
        error_str = cfd_python.get_error_string(0)
        bc_name = cfd_python.bc_get_backend_name()
        backend_name = cfd_python.backend_get_name(backend)
        simd_name = cfd_python.get_simd_name()

        # Check refcounts (Python may intern some strings, but shouldn't be excessive)
        for name, val in [
            ("error_str", error_str),
            ("bc_name", bc_name),
            ("backend_name", backend_name),
            ("simd_name", simd_name),
        ]:
            refcount = sys.getrefcount(val)
            # String interning can cause higher refcounts for common strings
            # but we check for excessively high counts that would indicate a bug
            assert refcount < 1000, f"Suspiciously high refcount for {name}: {refcount}"

    def test_refcount_for_returned_ints(self):
        """Test that returned ints have correct reference counts.

        Note: Python caches small integers (-5 to 256), so their refcounts can
        be extremely high (millions to billions). For values like 0, the refcount
        can exceed 1 billion due to internal Python usage. We only verify the
        functions return valid ints without crashing.
        """
        import sys

        import cfd_python

        # Get return values and verify they're valid integers
        status = cfd_python.get_last_status()
        backend = cfd_python.bc_get_backend()
        arch = cfd_python.get_simd_arch()

        # Verify all are valid integers (refcount check is not reliable for cached ints)
        assert isinstance(status, int)
        assert isinstance(backend, int)
        assert isinstance(arch, int)

        # These should be callable without segfaults
        _ = sys.getrefcount(status)
        _ = sys.getrefcount(backend)
        _ = sys.getrefcount(arch)
