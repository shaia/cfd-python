"""
Integration tests for complete workflows
"""
import pytest
import cfd_python


class TestIntegration:
    """Integration tests for complete workflows"""

    def test_full_simulation_workflow(self, tmp_path):
        """Test complete simulation workflow"""
        # 1. List available solvers
        solvers = cfd_python.list_solvers()
        assert len(solvers) > 0

        # 2. Get solver info
        solver_info = cfd_python.get_solver_info(solvers[0])
        assert 'name' in solver_info

        # 3. Get default parameters
        params = cfd_python.get_default_solver_params()
        assert 'dt' in params

        # 4. Create grid
        grid = cfd_python.create_grid(10, 10, 0.0, 1.0, 0.0, 1.0)
        assert grid['nx'] == 10

        # 5. Run simulation
        vtk_file = tmp_path / "workflow_test.vtk"
        result = cfd_python.run_simulation_with_params(
            10, 10, 0.0, 1.0, 0.0, 1.0,
            steps=5,
            solver_type=solvers[0],
            output_file=str(vtk_file)
        )

        # 6. Verify results
        assert 'velocity_magnitude' in result
        assert len(result['velocity_magnitude']) == 100
        assert vtk_file.exists()

    def test_solver_constant_matches_list(self):
        """Test that solver constants match list_solvers output"""
        solvers = cfd_python.list_solvers()

        for solver_name in solvers:
            # Use the constant to run a simulation
            const_name = 'SOLVER_' + solver_name.upper()
            if hasattr(cfd_python, const_name):
                solver_type = getattr(cfd_python, const_name)
                # Should be able to use this to check solver exists
                assert cfd_python.has_solver(solver_type)

    def test_multiple_simulations_same_grid(self):
        """Test running multiple simulations with same grid"""
        grid = cfd_python.create_grid(8, 8, 0.0, 1.0, 0.0, 1.0)

        results = []
        for i in range(3):
            result = cfd_python.run_simulation(
                grid['nx'], grid['ny'], steps=2
            )
            results.append(result)

        # All results should have same size
        for r in results:
            assert len(r) == 64

    def test_different_solvers_same_problem(self):
        """Test running same problem with different solvers"""
        solvers = cfd_python.list_solvers()

        results = {}
        for solver_name in solvers[:2]:  # Test first two solvers
            result = cfd_python.run_simulation(
                5, 5, steps=3, solver_type=solver_name
            )
            results[solver_name] = result

        # All results should have correct size
        for name, result in results.items():
            assert len(result) == 25, f"Solver {name} returned wrong size"

    def test_output_workflow(self, tmp_path):
        """Test complete output workflow"""
        # Set output directory
        cfd_python.set_output_dir(str(tmp_path))

        # Run simulation
        nx, ny = 6, 6
        result = cfd_python.run_simulation(nx, ny, steps=3)

        # Write VTK scalar output
        vtk_file = tmp_path / "velocity_mag.vtk"
        cfd_python.write_vtk_scalar(
            str(vtk_file), "velocity_magnitude", result,
            nx, ny, 0.0, 1.0, 0.0, 1.0
        )
        assert vtk_file.exists()

        # Write VTK vector output
        u_data = [0.1] * (nx * ny)
        v_data = [0.05] * (nx * ny)
        vtk_vector_file = tmp_path / "velocity.vtk"
        cfd_python.write_vtk_vector(
            str(vtk_vector_file), "velocity", u_data, v_data,
            nx, ny, 0.0, 1.0, 0.0, 1.0
        )
        assert vtk_vector_file.exists()

        # Write CSV timeseries
        csv_file = tmp_path / "timeseries.csv"
        p_data = [1.0] * (nx * ny)
        cfd_python.write_csv_timeseries(
            str(csv_file), step=0, time=0.0,
            u_data=u_data, v_data=v_data, p_data=p_data,
            nx=nx, ny=ny, dt=0.001, iterations=10,
            create_new=True
        )
        assert csv_file.exists()
