"""
Tests for solver discovery and dynamic solver constants
"""
import pytest
import cfd_python


class TestSolverDiscovery:
    """Test solver discovery functions"""

    def test_list_solvers_returns_list(self):
        """Test list_solvers returns a list"""
        solvers = cfd_python.list_solvers()
        assert isinstance(solvers, list)

    def test_list_solvers_not_empty(self):
        """Test at least one solver is available"""
        solvers = cfd_python.list_solvers()
        assert len(solvers) > 0, "At least one solver should be available"

    def test_list_solvers_contains_explicit_euler(self):
        """Test explicit_euler solver is available"""
        solvers = cfd_python.list_solvers()
        assert 'explicit_euler' in solvers, "explicit_euler should be a built-in solver"

    def test_has_solver_true(self):
        """Test has_solver returns True for existing solver"""
        assert cfd_python.has_solver('explicit_euler') is True

    def test_has_solver_false(self):
        """Test has_solver returns False for non-existing solver"""
        assert cfd_python.has_solver('nonexistent_solver_xyz') is False

    def test_get_solver_info_returns_dict(self):
        """Test get_solver_info returns a dictionary"""
        info = cfd_python.get_solver_info('explicit_euler')
        assert isinstance(info, dict)

    def test_get_solver_info_has_required_keys(self):
        """Test get_solver_info contains expected keys"""
        info = cfd_python.get_solver_info('explicit_euler')
        assert 'name' in info
        assert 'description' in info
        assert 'version' in info
        assert 'capabilities' in info

    def test_get_solver_info_capabilities_is_list(self):
        """Test solver capabilities is a list"""
        info = cfd_python.get_solver_info('explicit_euler')
        assert isinstance(info['capabilities'], list)

    def test_get_solver_info_invalid_solver(self):
        """Test get_solver_info raises error for invalid solver"""
        with pytest.raises(ValueError):
            cfd_python.get_solver_info('nonexistent_solver_xyz')


class TestDynamicSolverConstants:
    """Test dynamically generated SOLVER_* constants"""

    def test_solver_constants_exist(self):
        """Test SOLVER_* constants are dynamically created"""
        solvers = cfd_python.list_solvers()

        for solver_name in solvers:
            const_name = 'SOLVER_' + solver_name.upper()
            assert hasattr(cfd_python, const_name), f"Missing constant: {const_name}"

    def test_solver_constants_values(self):
        """Test SOLVER_* constants have correct values"""
        solvers = cfd_python.list_solvers()

        for solver_name in solvers:
            const_name = 'SOLVER_' + solver_name.upper()
            const_value = getattr(cfd_python, const_name)
            assert const_value == solver_name, f"{const_name} should equal '{solver_name}'"

    def test_explicit_euler_constant(self):
        """Test SOLVER_EXPLICIT_EULER constant specifically"""
        assert hasattr(cfd_python, 'SOLVER_EXPLICIT_EULER')
        assert cfd_python.SOLVER_EXPLICIT_EULER == 'explicit_euler'
