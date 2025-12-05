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
