"""
Tests for solver backend availability API in cfd_python (v0.1.6).
"""

import cfd_python


class TestBackendConstants:
    """Test BACKEND_* constants are defined and valid"""

    def test_backend_constants_exist(self):
        """Test all BACKEND_* constants are defined"""
        backends = [
            "BACKEND_SCALAR",
            "BACKEND_SIMD",
            "BACKEND_OMP",
            "BACKEND_CUDA",
        ]
        for const_name in backends:
            assert hasattr(cfd_python, const_name), f"Missing constant: {const_name}"

    def test_backend_constants_are_integers(self):
        """Test BACKEND_* constants are integers"""
        backends = [
            "BACKEND_SCALAR",
            "BACKEND_SIMD",
            "BACKEND_OMP",
            "BACKEND_CUDA",
        ]
        for const_name in backends:
            value = getattr(cfd_python, const_name)
            assert isinstance(value, int), f"{const_name} should be an integer"

    def test_backend_constants_unique(self):
        """Test BACKEND_* constants have unique values"""
        backends = [
            "BACKEND_SCALAR",
            "BACKEND_SIMD",
            "BACKEND_OMP",
            "BACKEND_CUDA",
        ]
        values = [getattr(cfd_python, name) for name in backends]
        assert len(values) == len(set(values)), "BACKEND_* constants should have unique values"

    def test_backend_constants_values(self):
        """Test BACKEND_* constants have expected values (matching C enum)"""
        assert cfd_python.BACKEND_SCALAR == 0
        assert cfd_python.BACKEND_SIMD == 1
        assert cfd_python.BACKEND_OMP == 2
        assert cfd_python.BACKEND_CUDA == 3


class TestBackendIsAvailable:
    """Test backend_is_available function"""

    def test_backend_is_available_returns_bool(self):
        """Test backend_is_available returns boolean for all backends"""
        for backend in [
            cfd_python.BACKEND_SCALAR,
            cfd_python.BACKEND_SIMD,
            cfd_python.BACKEND_OMP,
            cfd_python.BACKEND_CUDA,
        ]:
            result = cfd_python.backend_is_available(backend)
            assert isinstance(
                result, bool
            ), f"backend_is_available should return bool for {backend}"

    def test_scalar_backend_always_available(self):
        """Test SCALAR backend is always available"""
        available = cfd_python.backend_is_available(cfd_python.BACKEND_SCALAR)
        assert available is True, "SCALAR backend should always be available"

    def test_backend_is_available_invalid_backend(self):
        """Test backend_is_available with invalid backend returns False"""
        # Invalid backend ID should return False (not raise exception)
        result = cfd_python.backend_is_available(999)
        assert result is False


class TestBackendGetName:
    """Test backend_get_name function"""

    def test_backend_get_name_returns_string(self):
        """Test backend_get_name returns string for valid backends"""
        for backend in [
            cfd_python.BACKEND_SCALAR,
            cfd_python.BACKEND_SIMD,
            cfd_python.BACKEND_OMP,
            cfd_python.BACKEND_CUDA,
        ]:
            name = cfd_python.backend_get_name(backend)
            assert isinstance(name, str), f"backend_get_name should return string for {backend}"
            assert len(name) > 0, f"Backend name should not be empty for {backend}"

    def test_backend_get_name_expected_names(self):
        """Test backend_get_name returns expected name strings"""
        assert cfd_python.backend_get_name(cfd_python.BACKEND_SCALAR) == "scalar"
        assert cfd_python.backend_get_name(cfd_python.BACKEND_SIMD) == "simd"
        assert cfd_python.backend_get_name(cfd_python.BACKEND_OMP) == "omp"
        assert cfd_python.backend_get_name(cfd_python.BACKEND_CUDA) == "cuda"

    def test_backend_get_name_invalid_backend(self):
        """Test backend_get_name with invalid backend returns None"""
        result = cfd_python.backend_get_name(999)
        assert result is None


class TestListSolversByBackend:
    """Test list_solvers_by_backend function"""

    def test_list_solvers_by_backend_returns_list(self):
        """Test list_solvers_by_backend returns a list"""
        result = cfd_python.list_solvers_by_backend(cfd_python.BACKEND_SCALAR)
        assert isinstance(result, list), "list_solvers_by_backend should return a list"

    def test_list_solvers_by_backend_scalar_has_solvers(self):
        """Test SCALAR backend has at least one solver registered"""
        solvers = cfd_python.list_solvers_by_backend(cfd_python.BACKEND_SCALAR)
        assert len(solvers) > 0, "SCALAR backend should have at least one solver"

    def test_list_solvers_by_backend_returns_strings(self):
        """Test list_solvers_by_backend returns list of strings"""
        solvers = cfd_python.list_solvers_by_backend(cfd_python.BACKEND_SCALAR)
        for solver in solvers:
            assert isinstance(solver, str), f"Solver name should be string: {solver}"

    def test_list_solvers_by_backend_invalid_backend(self):
        """Test list_solvers_by_backend with invalid backend returns empty list"""
        result = cfd_python.list_solvers_by_backend(999)
        assert isinstance(result, list)
        assert len(result) == 0


class TestGetAvailableBackends:
    """Test get_available_backends function"""

    def test_get_available_backends_returns_list(self):
        """Test get_available_backends returns a list"""
        result = cfd_python.get_available_backends()
        assert isinstance(result, list), "get_available_backends should return a list"

    def test_get_available_backends_includes_scalar(self):
        """Test get_available_backends includes scalar (always available)"""
        backends = cfd_python.get_available_backends()
        assert "scalar" in backends, "SCALAR backend should always be in available list"

    def test_get_available_backends_returns_strings(self):
        """Test get_available_backends returns list of strings"""
        backends = cfd_python.get_available_backends()
        for backend in backends:
            assert isinstance(backend, str), f"Backend name should be string: {backend}"

    def test_get_available_backends_consistency(self):
        """Test get_available_backends is consistent with backend_is_available"""
        available_backends = cfd_python.get_available_backends()

        # Check each backend constant
        for backend_id, backend_name in [
            (cfd_python.BACKEND_SCALAR, "scalar"),
            (cfd_python.BACKEND_SIMD, "simd"),
            (cfd_python.BACKEND_OMP, "omp"),
            (cfd_python.BACKEND_CUDA, "cuda"),
        ]:
            is_available = cfd_python.backend_is_available(backend_id)
            in_list = backend_name in available_backends
            assert is_available == in_list, (
                f"Inconsistency for {backend_name}: "
                f"backend_is_available={is_available}, in list={in_list}"
            )


class TestBackendFunctionsExported:
    """Test that all backend functions are properly exported"""

    def test_backend_functions_in_all(self):
        """Test all backend functions are in __all__"""
        backend_functions = [
            "backend_is_available",
            "backend_get_name",
            "list_solvers_by_backend",
            "get_available_backends",
        ]
        for func_name in backend_functions:
            assert func_name in cfd_python.__all__, f"{func_name} should be in __all__"
            assert callable(getattr(cfd_python, func_name)), f"{func_name} should be callable"

    def test_backend_constants_in_all(self):
        """Test all BACKEND_* constants are in __all__"""
        backend_constants = [
            "BACKEND_SCALAR",
            "BACKEND_SIMD",
            "BACKEND_OMP",
            "BACKEND_CUDA",
        ]
        for const_name in backend_constants:
            assert const_name in cfd_python.__all__, f"{const_name} should be in __all__"
