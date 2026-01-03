"""
Tests for error handling
"""

import pytest

import cfd_python


class TestErrorHandling:
    """Test error handling"""

    def test_run_simulation_invalid_nx(self):
        """Test error handling for invalid nx type"""
        with pytest.raises(TypeError):
            cfd_python.run_simulation("invalid", 5, steps=3)

    def test_run_simulation_invalid_ny(self):
        """Test error handling for invalid ny type"""
        with pytest.raises(TypeError):
            cfd_python.run_simulation(5, "invalid", steps=3)

    def test_create_grid_invalid_params(self):
        """Test error handling for invalid grid parameters"""
        with pytest.raises(TypeError):
            cfd_python.create_grid("invalid", 10, 0.0, 1.0, 0.0, 1.0)

    def test_write_vtk_scalar_invalid_data_type(self, tmp_path):
        """Test error handling for invalid data type"""
        output_file = tmp_path / "invalid.vtk"
        with pytest.raises(TypeError):
            cfd_python.write_vtk_scalar(
                str(output_file), "test", "not a list", 5, 5, 0.0, 1.0, 0.0, 1.0
            )

    def test_has_solver_invalid_type(self):
        """Test error handling for invalid solver type argument"""
        with pytest.raises(TypeError):
            cfd_python.has_solver(123)  # Should be string

    def test_get_solver_info_empty_string(self):
        """Test error handling for empty solver name"""
        with pytest.raises(ValueError):
            cfd_python.get_solver_info("")

    def test_create_grid_zero_dimensions(self):
        """Test error handling for zero grid dimensions."""
        with pytest.raises(ValueError):
            cfd_python.create_grid(0, 10, 0.0, 1.0, 0.0, 1.0)

    def test_create_grid_negative_dimensions(self):
        """Test error handling for negative grid dimensions."""
        with pytest.raises(ValueError):
            cfd_python.create_grid(-5, 10, 0.0, 1.0, 0.0, 1.0)

    def test_run_simulation_zero_steps(self):
        """Test that zero steps simulation returns valid grid."""
        # Zero steps is allowed - returns initial grid state
        result = cfd_python.run_simulation(5, 5, steps=0)
        assert isinstance(result, list)
        assert len(result) == 25  # 5x5 grid


class TestExceptionClasses:
    """Test exception class hierarchy and attributes"""

    def test_cfd_error_base(self):
        """Test CFDError base class"""
        err = cfd_python.CFDError("test error", -1)
        assert err.message == "test error"
        assert err.status_code == -1
        assert "test error" in str(err)
        assert "(status=-1)" in str(err)

    def test_cfd_error_default_status(self):
        """Test CFDError with default status code"""
        err = cfd_python.CFDError("test error")
        assert err.status_code == -1

    def test_cfd_memory_error_inheritance(self):
        """Test CFDMemoryError inherits from both CFDError and MemoryError"""
        err = cfd_python.CFDMemoryError("out of memory", -2)
        assert isinstance(err, cfd_python.CFDError)
        assert isinstance(err, MemoryError)
        assert err.status_code == -2

    def test_cfd_invalid_error_inheritance(self):
        """Test CFDInvalidError inherits from both CFDError and ValueError"""
        err = cfd_python.CFDInvalidError("invalid argument", -3)
        assert isinstance(err, cfd_python.CFDError)
        assert isinstance(err, ValueError)
        assert err.status_code == -3

    def test_cfd_io_error_inheritance(self):
        """Test CFDIOError inherits from both CFDError and OSError"""
        err = cfd_python.CFDIOError("file not found", -4)
        assert isinstance(err, cfd_python.CFDError)
        assert isinstance(err, OSError)
        assert err.status_code == -4

    def test_cfd_unsupported_error_inheritance(self):
        """Test CFDUnsupportedError inherits from both CFDError and NotImplementedError"""
        err = cfd_python.CFDUnsupportedError("not supported", -5)
        assert isinstance(err, cfd_python.CFDError)
        assert isinstance(err, NotImplementedError)
        assert err.status_code == -5

    def test_cfd_diverged_error(self):
        """Test CFDDivergedError"""
        err = cfd_python.CFDDivergedError("solver diverged", -6)
        assert isinstance(err, cfd_python.CFDError)
        assert err.status_code == -6

    def test_cfd_max_iter_error(self):
        """Test CFDMaxIterError"""
        err = cfd_python.CFDMaxIterError("max iterations reached", -7)
        assert isinstance(err, cfd_python.CFDError)
        assert err.status_code == -7


class TestRaiseForStatus:
    """Test raise_for_status function"""

    def test_success_does_not_raise(self):
        """Test that success status codes do not raise"""
        cfd_python.raise_for_status(0)  # CFD_SUCCESS
        cfd_python.raise_for_status(1)  # Any positive value

    def test_generic_error_raises_cfd_error(self):
        """Test that -1 raises CFDError"""
        with pytest.raises(cfd_python.CFDError) as exc_info:
            cfd_python.raise_for_status(-1)
        assert exc_info.value.status_code == -1

    def test_nomem_raises_cfd_memory_error(self):
        """Test that -2 raises CFDMemoryError"""
        with pytest.raises(cfd_python.CFDMemoryError) as exc_info:
            cfd_python.raise_for_status(-2)
        assert exc_info.value.status_code == -2

    def test_invalid_raises_cfd_invalid_error(self):
        """Test that -3 raises CFDInvalidError"""
        with pytest.raises(cfd_python.CFDInvalidError) as exc_info:
            cfd_python.raise_for_status(-3)
        assert exc_info.value.status_code == -3

    def test_io_raises_cfd_io_error(self):
        """Test that -4 raises CFDIOError"""
        with pytest.raises(cfd_python.CFDIOError) as exc_info:
            cfd_python.raise_for_status(-4)
        assert exc_info.value.status_code == -4

    def test_unsupported_raises_cfd_unsupported_error(self):
        """Test that -5 raises CFDUnsupportedError"""
        with pytest.raises(cfd_python.CFDUnsupportedError) as exc_info:
            cfd_python.raise_for_status(-5)
        assert exc_info.value.status_code == -5

    def test_diverged_raises_cfd_diverged_error(self):
        """Test that -6 raises CFDDivergedError"""
        with pytest.raises(cfd_python.CFDDivergedError) as exc_info:
            cfd_python.raise_for_status(-6)
        assert exc_info.value.status_code == -6

    def test_max_iter_raises_cfd_max_iter_error(self):
        """Test that -7 raises CFDMaxIterError"""
        with pytest.raises(cfd_python.CFDMaxIterError) as exc_info:
            cfd_python.raise_for_status(-7)
        assert exc_info.value.status_code == -7

    def test_unknown_error_raises_cfd_error(self):
        """Test that unknown negative codes raise CFDError"""
        with pytest.raises(cfd_python.CFDError) as exc_info:
            cfd_python.raise_for_status(-99)
        assert exc_info.value.status_code == -99

    def test_context_included_in_message(self):
        """Test that context is included in error message"""
        with pytest.raises(cfd_python.CFDError) as exc_info:
            cfd_python.raise_for_status(-1, "during simulation")
        assert "during simulation" in str(exc_info.value)


class TestExceptionExports:
    """Test that exception classes are properly exported"""

    def test_exceptions_in_all(self):
        """Test all exception classes are in __all__"""
        exceptions = [
            "CFDError",
            "CFDMemoryError",
            "CFDInvalidError",
            "CFDIOError",
            "CFDUnsupportedError",
            "CFDDivergedError",
            "CFDMaxIterError",
            "raise_for_status",
        ]
        for name in exceptions:
            assert name in cfd_python.__all__, f"{name} should be in __all__"
            assert hasattr(cfd_python, name), f"{name} should be accessible"
