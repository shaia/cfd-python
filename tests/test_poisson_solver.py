"""Tests for Poisson solver functions and constants (v0.2.0)."""

import cfd_python


class TestPoissonMethodConstants:
    """Tests for POISSON_METHOD_* constants."""

    _METHODS = [
        "POISSON_METHOD_JACOBI",
        "POISSON_METHOD_GAUSS_SEIDEL",
        "POISSON_METHOD_SOR",
        "POISSON_METHOD_REDBLACK_SOR",
        "POISSON_METHOD_CG",
        "POISSON_METHOD_BICGSTAB",
        "POISSON_METHOD_MULTIGRID",
    ]

    def test_method_constants_exist(self):
        for name in self._METHODS:
            assert hasattr(cfd_python, name), f"Missing: {name}"

    def test_method_constants_are_integers(self):
        for name in self._METHODS:
            assert isinstance(getattr(cfd_python, name), int)

    def test_method_constants_unique(self):
        values = [getattr(cfd_python, name) for name in self._METHODS]
        assert len(values) == len(set(values)), "Duplicate method constant values"

    def test_method_constants_in_all(self):
        for name in self._METHODS:
            assert name in cfd_python.__all__, f"{name} not in __all__"


class TestPoissonBackendConstants:
    """Tests for POISSON_BACKEND_* constants."""

    _BACKENDS = [
        "POISSON_BACKEND_AUTO",
        "POISSON_BACKEND_SCALAR",
        "POISSON_BACKEND_OMP",
        "POISSON_BACKEND_SIMD",
        "POISSON_BACKEND_GPU",
    ]

    def test_backend_constants_exist(self):
        for name in self._BACKENDS:
            assert hasattr(cfd_python, name), f"Missing: {name}"

    def test_backend_constants_are_integers(self):
        for name in self._BACKENDS:
            assert isinstance(getattr(cfd_python, name), int)

    def test_backend_constants_unique(self):
        values = [getattr(cfd_python, name) for name in self._BACKENDS]
        assert len(values) == len(set(values)), "Duplicate backend constant values"

    def test_backend_constants_in_all(self):
        for name in self._BACKENDS:
            assert name in cfd_python.__all__, f"{name} not in __all__"


class TestPoissonSolverPresets:
    """Tests for POISSON_SOLVER_* preset constants."""

    _PRESETS = [
        "POISSON_SOLVER_SOR_SCALAR",
        "POISSON_SOLVER_JACOBI_SIMD",
        "POISSON_SOLVER_REDBLACK_SIMD",
        "POISSON_SOLVER_REDBLACK_OMP",
        "POISSON_SOLVER_REDBLACK_SCALAR",
        "POISSON_SOLVER_CG_SCALAR",
        "POISSON_SOLVER_CG_SIMD",
        "POISSON_SOLVER_CG_OMP",
    ]

    def test_solver_preset_constants_exist(self):
        for name in self._PRESETS:
            assert hasattr(cfd_python, name), f"Missing: {name}"

    def test_solver_preset_constants_are_integers(self):
        for name in self._PRESETS:
            assert isinstance(getattr(cfd_python, name), int)

    def test_solver_preset_constants_unique(self):
        values = [getattr(cfd_python, name) for name in self._PRESETS]
        assert len(values) == len(set(values)), "Duplicate solver preset values"


class TestPoissonPrecondConstants:
    """Tests for POISSON_PRECOND_* constants."""

    _PRECONDS = ["POISSON_PRECOND_NONE", "POISSON_PRECOND_JACOBI"]

    def test_precond_constants_exist(self):
        for name in self._PRECONDS:
            assert hasattr(cfd_python, name), f"Missing: {name}"

    def test_precond_constants_are_integers(self):
        for name in self._PRECONDS:
            assert isinstance(getattr(cfd_python, name), int)

    def test_precond_constants_unique(self):
        values = [getattr(cfd_python, name) for name in self._PRECONDS]
        assert len(values) == len(set(values)), "Duplicate preconditioner constant values"

    def test_precond_constants_in_all(self):
        for name in self._PRECONDS:
            assert name in cfd_python.__all__, f"{name} not in __all__"


class TestPoissonFunctions:
    """Tests for Poisson solver query and configuration functions."""

    def test_get_default_poisson_params_returns_dict(self):
        result = cfd_python.get_default_poisson_params()
        assert isinstance(result, dict)

    def test_default_params_has_expected_keys(self):
        params = cfd_python.get_default_poisson_params()
        expected = {
            "tolerance",
            "absolute_tolerance",
            "max_iterations",
            "omega",
            "check_interval",
            "verbose",
            "preconditioner",
        }
        for key in expected:
            assert key in params, f"Missing key: {key}"

    def test_default_params_tolerance_positive(self):
        params = cfd_python.get_default_poisson_params()
        assert params["tolerance"] > 0

    def test_default_params_max_iterations_positive(self):
        params = cfd_python.get_default_poisson_params()
        assert params["max_iterations"] > 0

    def test_poisson_get_backend_returns_int(self):
        result = cfd_python.poisson_get_backend()
        assert isinstance(result, int)

    def test_poisson_get_backend_name_returns_string(self):
        result = cfd_python.poisson_get_backend_name()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_poisson_backend_available_returns_bool(self):
        result = cfd_python.poisson_backend_available(cfd_python.POISSON_BACKEND_SCALAR)
        assert isinstance(result, bool)

    def test_poisson_scalar_backend_always_available(self):
        assert cfd_python.poisson_backend_available(cfd_python.POISSON_BACKEND_SCALAR)

    def test_poisson_set_backend_scalar(self):
        original = cfd_python.poisson_get_backend()
        result = cfd_python.poisson_set_backend(cfd_python.POISSON_BACKEND_SCALAR)
        assert isinstance(result, bool)
        cfd_python.poisson_set_backend(original)  # restore

    def test_poisson_simd_available_returns_bool(self):
        result = cfd_python.poisson_simd_available()
        assert isinstance(result, bool)

    def test_poisson_functions_repeated_calls(self):
        """Verify no crashes or leaks under repeated Poisson function calls."""
        for _ in range(50):
            cfd_python.get_default_poisson_params()
            cfd_python.poisson_get_backend()
            cfd_python.poisson_get_backend_name()

    def test_poisson_set_backend_invalid_returns_false(self):
        """Test setting an invalid backend returns False."""
        result = cfd_python.poisson_set_backend(9999)
        assert result is False

    def test_poisson_backend_available_invalid_returns_false(self):
        """Test invalid backend is not available."""
        result = cfd_python.poisson_backend_available(9999)
        assert result is False

    def test_poisson_functions_in_all(self):
        funcs = [
            "get_default_poisson_params",
            "poisson_get_backend",
            "poisson_get_backend_name",
            "poisson_set_backend",
            "poisson_backend_available",
            "poisson_simd_available",
        ]
        for name in funcs:
            assert name in cfd_python.__all__, f"{name} not in __all__"
