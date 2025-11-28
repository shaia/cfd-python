"""
Tests for simulation functions (grid, params, run_simulation)
"""
import pytest
import cfd_python


class TestGrid:
    """Test grid creation function"""

    def test_create_grid_returns_dict(self):
        """Test create_grid returns a dictionary"""
        grid = cfd_python.create_grid(10, 10, 0.0, 1.0, 0.0, 1.0)
        assert isinstance(grid, dict)

    def test_create_grid_has_dimensions(self):
        """Test create_grid result contains dimensions"""
        grid = cfd_python.create_grid(10, 20, 0.0, 1.0, 0.0, 2.0)
        assert grid['nx'] == 10
        assert grid['ny'] == 20

    def test_create_grid_has_bounds(self):
        """Test create_grid result contains domain bounds"""
        grid = cfd_python.create_grid(10, 10, -1.0, 1.0, -2.0, 2.0)
        assert grid['xmin'] == -1.0
        assert grid['xmax'] == 1.0
        assert grid['ymin'] == -2.0
        assert grid['ymax'] == 2.0

    def test_create_grid_has_coordinates(self):
        """Test create_grid result contains coordinate arrays"""
        grid = cfd_python.create_grid(5, 3, 0.0, 1.0, 0.0, 1.0)
        assert 'x_coords' in grid
        assert 'y_coords' in grid
        assert len(grid['x_coords']) == 5
        assert len(grid['y_coords']) == 3


class TestSolverParams:
    """Test solver parameters function"""

    def test_get_default_solver_params_returns_dict(self):
        """Test get_default_solver_params returns a dictionary"""
        params = cfd_python.get_default_solver_params()
        assert isinstance(params, dict)

    def test_default_params_has_dt(self):
        """Test default params contains dt"""
        params = cfd_python.get_default_solver_params()
        assert 'dt' in params
        assert isinstance(params['dt'], float)
        assert params['dt'] > 0

    def test_default_params_has_cfl(self):
        """Test default params contains cfl"""
        params = cfd_python.get_default_solver_params()
        assert 'cfl' in params
        assert isinstance(params['cfl'], float)
        assert 0 < params['cfl'] < 1

    def test_default_params_has_all_keys(self):
        """Test default params contains all expected keys"""
        params = cfd_python.get_default_solver_params()
        expected_keys = ['dt', 'cfl', 'gamma', 'mu', 'k', 'max_iter', 'tolerance']
        for key in expected_keys:
            assert key in params, f"Missing parameter: {key}"


class TestRunSimulation:
    """Test run_simulation function"""

    def test_run_simulation_returns_list(self):
        """Test run_simulation returns velocity magnitude list"""
        result = cfd_python.run_simulation(5, 5, steps=3)
        assert isinstance(result, list)

    def test_run_simulation_result_size(self):
        """Test run_simulation result has correct size"""
        nx, ny = 5, 7
        result = cfd_python.run_simulation(nx, ny, steps=3)
        assert len(result) == nx * ny

    def test_run_simulation_non_negative_values(self):
        """Test velocity magnitudes are non-negative"""
        result = cfd_python.run_simulation(5, 5, steps=3)
        for v in result:
            assert v >= 0.0, "Velocity magnitude should be non-negative"

    def test_run_simulation_with_solver_type(self):
        """Test run_simulation with explicit solver type"""
        result = cfd_python.run_simulation(5, 5, steps=3, solver_type='explicit_euler')
        assert isinstance(result, list)
        assert len(result) == 25

    def test_run_simulation_with_domain_bounds(self):
        """Test run_simulation with custom domain bounds"""
        result = cfd_python.run_simulation(
            5, 5, steps=3,
            xmin=-1.0, xmax=1.0,
            ymin=-1.0, ymax=1.0
        )
        assert isinstance(result, list)

    def test_run_simulation_with_output_file(self, tmp_path):
        """Test run_simulation with VTK output"""
        output_file = tmp_path / "test_output.vtk"
        result = cfd_python.run_simulation(
            5, 5, steps=3,
            output_file=str(output_file)
        )
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_run_simulation_invalid_solver(self):
        """Test run_simulation with invalid solver raises error"""
        with pytest.raises(RuntimeError):
            cfd_python.run_simulation(5, 5, steps=3, solver_type='nonexistent_solver')


class TestRunSimulationWithParams:
    """Test run_simulation_with_params function"""

    def test_returns_dict(self):
        """Test run_simulation_with_params returns a dictionary"""
        result = cfd_python.run_simulation_with_params(
            5, 5, 0.0, 1.0, 0.0, 1.0, steps=3
        )
        assert isinstance(result, dict)

    def test_result_has_velocity_magnitude(self):
        """Test result contains velocity_magnitude"""
        result = cfd_python.run_simulation_with_params(
            5, 5, 0.0, 1.0, 0.0, 1.0, steps=3
        )
        assert 'velocity_magnitude' in result
        assert isinstance(result['velocity_magnitude'], list)

    def test_result_has_dimensions(self):
        """Test result contains grid dimensions"""
        result = cfd_python.run_simulation_with_params(
            5, 7, 0.0, 1.0, 0.0, 1.0, steps=3
        )
        assert result['nx'] == 5
        assert result['ny'] == 7

    def test_result_has_solver_info(self):
        """Test result contains solver information"""
        result = cfd_python.run_simulation_with_params(
            5, 5, 0.0, 1.0, 0.0, 1.0, steps=3
        )
        assert 'solver_name' in result

    def test_result_has_stats(self):
        """Test result contains solver statistics"""
        result = cfd_python.run_simulation_with_params(
            5, 5, 0.0, 1.0, 0.0, 1.0, steps=3
        )
        assert 'stats' in result
        stats = result['stats']
        assert 'iterations' in stats
        assert 'max_velocity' in stats
        assert 'max_pressure' in stats

    def test_custom_dt_and_cfl(self):
        """Test custom dt and cfl parameters"""
        result = cfd_python.run_simulation_with_params(
            5, 5, 0.0, 1.0, 0.0, 1.0,
            steps=3, dt=0.0005, cfl=0.1
        )
        assert isinstance(result, dict)

    def test_with_output_file(self, tmp_path):
        """Test with VTK output file"""
        output_file = tmp_path / "detailed_output.vtk"
        result = cfd_python.run_simulation_with_params(
            5, 5, 0.0, 1.0, 0.0, 1.0,
            steps=3, output_file=str(output_file)
        )
        assert 'output_file' in result
        assert output_file.exists()
