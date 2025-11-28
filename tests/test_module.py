"""
Tests for module-level attributes and exports
"""
import re
import cfd_python


class TestModuleAttributes:
    """Test module-level attributes and constants"""

    def test_version_exists_and_valid_format(self):
        """Test version string exists and follows semantic versioning"""
        assert hasattr(cfd_python, '__version__')
        version = cfd_python.__version__
        assert isinstance(version, str)
        assert len(version) > 0, "Version string should not be empty"
        # Version should match semantic versioning pattern (with optional pre-release/build metadata)
        # Examples: "0.3.0", "1.0.0", "0.1.0.dev1", "0.3.0+g1234567"
        semver_pattern = r'^\d+\.\d+\.\d+.*$'
        assert re.match(semver_pattern, version), \
            f"Version '{version}' should follow semantic versioning (X.Y.Z)"

    def test_output_constants_exist(self):
        """Test OUTPUT_* constants are defined"""
        assert hasattr(cfd_python, 'OUTPUT_PRESSURE')
        assert hasattr(cfd_python, 'OUTPUT_VELOCITY')
        assert hasattr(cfd_python, 'OUTPUT_FULL_FIELD')
        assert hasattr(cfd_python, 'OUTPUT_CSV_TIMESERIES')
        assert hasattr(cfd_python, 'OUTPUT_CSV_CENTERLINE')
        assert hasattr(cfd_python, 'OUTPUT_CSV_STATISTICS')

    def test_output_constants_are_integers(self):
        """Test OUTPUT_* constants are integers"""
        assert isinstance(cfd_python.OUTPUT_PRESSURE, int)
        assert isinstance(cfd_python.OUTPUT_VELOCITY, int)
        assert isinstance(cfd_python.OUTPUT_FULL_FIELD, int)
        assert isinstance(cfd_python.OUTPUT_CSV_TIMESERIES, int)
        assert isinstance(cfd_python.OUTPUT_CSV_CENTERLINE, int)
        assert isinstance(cfd_python.OUTPUT_CSV_STATISTICS, int)

    def test_output_constants_unique(self):
        """Test OUTPUT_* constants have unique values"""
        values = [
            cfd_python.OUTPUT_PRESSURE,
            cfd_python.OUTPUT_VELOCITY,
            cfd_python.OUTPUT_FULL_FIELD,
            cfd_python.OUTPUT_CSV_TIMESERIES,
            cfd_python.OUTPUT_CSV_CENTERLINE,
            cfd_python.OUTPUT_CSV_STATISTICS,
        ]
        assert len(values) == len(set(values)), "OUTPUT_* constants should have unique values"


class TestAllExports:
    """Test that __all__ exports are accessible"""

    def test_core_functions_exported(self):
        """Test core functions are in __all__ and accessible"""
        core_functions = [
            'run_simulation',
            'create_grid',
            'get_default_solver_params',
            'run_simulation_with_params',
            'list_solvers',
            'has_solver',
            'get_solver_info',
            'set_output_dir',
            'write_vtk_scalar',
            'write_vtk_vector',
            'write_csv_timeseries',
        ]
        for func_name in core_functions:
            assert hasattr(cfd_python, func_name), f"Missing function: {func_name}"
            assert callable(getattr(cfd_python, func_name)), f"{func_name} should be callable"

    def test_output_constants_in_all(self):
        """Test OUTPUT_* constants are exported"""
        output_constants = [
            'OUTPUT_PRESSURE',
            'OUTPUT_VELOCITY',
            'OUTPUT_FULL_FIELD',
            'OUTPUT_CSV_TIMESERIES',
            'OUTPUT_CSV_CENTERLINE',
            'OUTPUT_CSV_STATISTICS',
        ]
        for const_name in output_constants:
            assert const_name in cfd_python.__all__, f"{const_name} should be in __all__"
