"""
Tests for boundary condition bindings in cfd_python.
"""

import cfd_python


class TestBCTypeConstants:
    """Test BC_TYPE_* constants are defined and valid"""

    def test_bc_type_constants_exist(self):
        """Test all BC_TYPE_* constants are defined"""
        bc_types = [
            "BC_TYPE_PERIODIC",
            "BC_TYPE_NEUMANN",
            "BC_TYPE_DIRICHLET",
            "BC_TYPE_NOSLIP",
            "BC_TYPE_INLET",
            "BC_TYPE_OUTLET",
        ]
        for const_name in bc_types:
            assert hasattr(cfd_python, const_name), f"Missing constant: {const_name}"

    def test_bc_type_constants_are_integers(self):
        """Test BC_TYPE_* constants are integers"""
        bc_types = [
            "BC_TYPE_PERIODIC",
            "BC_TYPE_NEUMANN",
            "BC_TYPE_DIRICHLET",
            "BC_TYPE_NOSLIP",
            "BC_TYPE_INLET",
            "BC_TYPE_OUTLET",
        ]
        for const_name in bc_types:
            value = getattr(cfd_python, const_name)
            assert isinstance(value, int), f"{const_name} should be an integer"

    def test_bc_type_constants_unique(self):
        """Test BC_TYPE_* constants have unique values"""
        bc_types = [
            "BC_TYPE_PERIODIC",
            "BC_TYPE_NEUMANN",
            "BC_TYPE_DIRICHLET",
            "BC_TYPE_NOSLIP",
            "BC_TYPE_INLET",
            "BC_TYPE_OUTLET",
        ]
        values = [getattr(cfd_python, name) for name in bc_types]
        assert len(values) == len(set(values)), "BC_TYPE_* constants should have unique values"


class TestBCEdgeConstants:
    """Test BC_EDGE_* constants are defined and valid"""

    def test_bc_edge_constants_exist(self):
        """Test all BC_EDGE_* constants are defined"""
        bc_edges = [
            "BC_EDGE_LEFT",
            "BC_EDGE_RIGHT",
            "BC_EDGE_BOTTOM",
            "BC_EDGE_TOP",
        ]
        for const_name in bc_edges:
            assert hasattr(cfd_python, const_name), f"Missing constant: {const_name}"

    def test_bc_edge_constants_are_integers(self):
        """Test BC_EDGE_* constants are integers"""
        bc_edges = [
            "BC_EDGE_LEFT",
            "BC_EDGE_RIGHT",
            "BC_EDGE_BOTTOM",
            "BC_EDGE_TOP",
        ]
        for const_name in bc_edges:
            value = getattr(cfd_python, const_name)
            assert isinstance(value, int), f"{const_name} should be an integer"

    def test_bc_edge_constants_unique(self):
        """Test BC_EDGE_* constants have unique values"""
        bc_edges = [
            "BC_EDGE_LEFT",
            "BC_EDGE_RIGHT",
            "BC_EDGE_BOTTOM",
            "BC_EDGE_TOP",
        ]
        values = [getattr(cfd_python, name) for name in bc_edges]
        assert len(values) == len(set(values)), "BC_EDGE_* constants should have unique values"


class TestBCBackendConstants:
    """Test BC_BACKEND_* constants are defined and valid"""

    def test_bc_backend_constants_exist(self):
        """Test all BC_BACKEND_* constants are defined"""
        bc_backends = [
            "BC_BACKEND_AUTO",
            "BC_BACKEND_SCALAR",
            "BC_BACKEND_OMP",
            "BC_BACKEND_SIMD",
            "BC_BACKEND_CUDA",
        ]
        for const_name in bc_backends:
            assert hasattr(cfd_python, const_name), f"Missing constant: {const_name}"

    def test_bc_backend_constants_are_integers(self):
        """Test BC_BACKEND_* constants are integers"""
        bc_backends = [
            "BC_BACKEND_AUTO",
            "BC_BACKEND_SCALAR",
            "BC_BACKEND_OMP",
            "BC_BACKEND_SIMD",
            "BC_BACKEND_CUDA",
        ]
        for const_name in bc_backends:
            value = getattr(cfd_python, const_name)
            assert isinstance(value, int), f"{const_name} should be an integer"

    def test_bc_backend_constants_unique(self):
        """Test BC_BACKEND_* constants have unique values"""
        bc_backends = [
            "BC_BACKEND_AUTO",
            "BC_BACKEND_SCALAR",
            "BC_BACKEND_OMP",
            "BC_BACKEND_SIMD",
            "BC_BACKEND_CUDA",
        ]
        values = [getattr(cfd_python, name) for name in bc_backends]
        assert len(values) == len(set(values)), "BC_BACKEND_* constants should have unique values"


class TestBCBackendFunctions:
    """Test boundary condition backend management functions"""

    def test_bc_get_backend(self):
        """Test bc_get_backend returns an integer"""
        backend = cfd_python.bc_get_backend()
        assert isinstance(backend, int), "bc_get_backend should return an integer"

    def test_bc_get_backend_name(self):
        """Test bc_get_backend_name returns a string"""
        name = cfd_python.bc_get_backend_name()
        assert isinstance(name, str), "bc_get_backend_name should return a string"
        assert len(name) > 0, "Backend name should not be empty"

    def test_bc_set_backend_scalar(self):
        """Test setting backend to SCALAR"""
        # Save original backend
        original = cfd_python.bc_get_backend()

        # Set to SCALAR (always available)
        result = cfd_python.bc_set_backend(cfd_python.BC_BACKEND_SCALAR)
        assert result is True, "Setting SCALAR backend should succeed"

        # Verify it was set
        current = cfd_python.bc_get_backend()
        assert current == cfd_python.BC_BACKEND_SCALAR

        # Restore original backend
        cfd_python.bc_set_backend(original)

    def test_bc_backend_available_scalar(self):
        """Test SCALAR backend is always available"""
        available = cfd_python.bc_backend_available(cfd_python.BC_BACKEND_SCALAR)
        assert available is True, "SCALAR backend should always be available"

    def test_bc_backend_available_returns_bool(self):
        """Test bc_backend_available returns boolean"""
        for backend in [
            cfd_python.BC_BACKEND_SCALAR,
            cfd_python.BC_BACKEND_OMP,
            cfd_python.BC_BACKEND_SIMD,
            cfd_python.BC_BACKEND_CUDA,
        ]:
            result = cfd_python.bc_backend_available(backend)
            assert isinstance(
                result, bool
            ), f"bc_backend_available should return bool for {backend}"


class TestBCApplyScalar:
    """Test bc_apply_scalar function"""

    def test_bc_apply_scalar_neumann(self):
        """Test applying Neumann BC to a scalar field"""
        # Create a 4x4 field (flat list)
        nx, ny = 4, 4
        field = [float(i) for i in range(nx * ny)]

        # Apply Neumann (zero-gradient) BC
        result = cfd_python.bc_apply_scalar(field, nx, ny, cfd_python.BC_TYPE_NEUMANN)
        assert result is None  # Returns None on success
        # Field should be modified in place
        assert len(field) == nx * ny

    def test_bc_apply_scalar_periodic(self):
        """Test applying Periodic BC to a scalar field"""
        nx, ny = 4, 4
        field = [float(i) for i in range(nx * ny)]

        result = cfd_python.bc_apply_scalar(field, nx, ny, cfd_python.BC_TYPE_PERIODIC)
        assert result is None

    def test_bc_apply_scalar_invalid_size(self):
        """Test bc_apply_scalar with mismatched size raises error"""
        import pytest

        nx, ny = 4, 4
        field = [0.0] * 8  # Wrong size (should be 16)

        with pytest.raises(ValueError):
            cfd_python.bc_apply_scalar(field, nx, ny, cfd_python.BC_TYPE_NEUMANN)


class TestBCApplyVelocity:
    """Test bc_apply_velocity function"""

    def test_bc_apply_velocity_neumann(self):
        """Test applying Neumann BC to velocity fields"""
        nx, ny = 4, 4
        size = nx * ny
        u = [1.0] * size
        v = [0.5] * size

        result = cfd_python.bc_apply_velocity(u, v, nx, ny, cfd_python.BC_TYPE_NEUMANN)
        assert result is None
        assert len(u) == size
        assert len(v) == size

    def test_bc_apply_velocity_periodic(self):
        """Test applying Periodic BC to velocity fields"""
        nx, ny = 4, 4
        size = nx * ny
        u = [1.0] * size
        v = [0.5] * size

        result = cfd_python.bc_apply_velocity(u, v, nx, ny, cfd_python.BC_TYPE_PERIODIC)
        assert result is None


class TestBCApplyDirichlet:
    """Test bc_apply_dirichlet function"""

    def test_bc_apply_dirichlet_fixed_values(self):
        """Test applying Dirichlet BC with fixed boundary values"""
        nx, ny = 4, 4
        field = [0.0] * (nx * ny)

        # Set fixed values at boundaries
        left, right, bottom, top = 1.0, 2.0, 3.0, 4.0
        result = cfd_python.bc_apply_dirichlet(field, nx, ny, left, right, bottom, top)
        assert result is None

        # Check interior left boundary (excluding corners where bottom/top may take priority)
        for j in range(1, ny - 1):
            assert field[j * nx + 0] == left, f"Left boundary at row {j}"

        # Check interior right boundary (excluding corners)
        for j in range(1, ny - 1):
            assert field[j * nx + (nx - 1)] == right, f"Right boundary at row {j}"

        # Bottom boundary (row 0) - full row including corners
        for i in range(nx):
            assert field[0 * nx + i] == bottom, f"Bottom boundary at col {i}"

        # Top boundary (row ny-1) - full row including corners
        for i in range(nx):
            assert field[(ny - 1) * nx + i] == top, f"Top boundary at col {i}"


class TestBCApplyNoslip:
    """Test bc_apply_noslip function"""

    def test_bc_apply_noslip_zeros_boundaries(self):
        """Test no-slip BC sets boundary velocities to zero"""
        nx, ny = 4, 4
        size = nx * ny
        u = [1.0] * size
        v = [1.0] * size

        result = cfd_python.bc_apply_noslip(u, v, nx, ny)
        assert result is None

        # Check all boundary values are zero
        # Left boundary
        for j in range(ny):
            idx = j * nx + 0
            assert u[idx] == 0.0, f"u left boundary at {j}"
            assert v[idx] == 0.0, f"v left boundary at {j}"

        # Right boundary
        for j in range(ny):
            idx = j * nx + (nx - 1)
            assert u[idx] == 0.0, f"u right boundary at {j}"
            assert v[idx] == 0.0, f"v right boundary at {j}"

        # Bottom boundary
        for i in range(nx):
            idx = 0 * nx + i
            assert u[idx] == 0.0, f"u bottom boundary at {i}"
            assert v[idx] == 0.0, f"v bottom boundary at {i}"

        # Top boundary
        for i in range(nx):
            idx = (ny - 1) * nx + i
            assert u[idx] == 0.0, f"u top boundary at {i}"
            assert v[idx] == 0.0, f"v top boundary at {i}"


class TestBCApplyInlet:
    """Test inlet boundary condition functions"""

    def test_bc_apply_inlet_uniform_left(self):
        """Test uniform inlet on left edge"""
        nx, ny = 4, 4
        size = nx * ny
        u = [0.0] * size
        v = [0.0] * size
        u_inlet, v_inlet = 1.0, 0.0

        result = cfd_python.bc_apply_inlet_uniform(
            u, v, nx, ny, u_inlet, v_inlet, cfd_python.BC_EDGE_LEFT
        )
        assert result is None

        # Check left boundary has inlet velocity
        for j in range(ny):
            idx = j * nx + 0
            assert u[idx] == u_inlet, f"u inlet at {j}"
            assert v[idx] == v_inlet, f"v inlet at {j}"

    def test_bc_apply_inlet_parabolic_left(self):
        """Test parabolic inlet profile on left edge"""
        nx, ny = 8, 8
        size = nx * ny
        u = [0.0] * size
        v = [0.0] * size
        max_velocity = 1.0

        result = cfd_python.bc_apply_inlet_parabolic(
            u, v, nx, ny, max_velocity, cfd_python.BC_EDGE_LEFT
        )
        assert result is None

        # Check parabolic profile: max at center, zero at walls
        # Left boundary values should follow parabolic pattern
        left_u = [u[j * nx + 0] for j in range(ny)]

        # The profile should peak near center
        # Middle values should be higher than edge values
        assert left_u[ny // 2] >= left_u[0], "Parabolic profile should peak near center"
        assert left_u[ny // 2] >= left_u[ny - 1], "Parabolic profile should peak near center"


class TestBCApplyOutlet:
    """Test outlet boundary condition functions"""

    def test_bc_apply_outlet_scalar_right(self):
        """Test zero-gradient outlet for scalar on right edge"""
        nx, ny = 4, 4
        size = nx * ny
        # Create field with gradient
        field = [float(i % nx) for i in range(size)]

        result = cfd_python.bc_apply_outlet_scalar(field, nx, ny, cfd_python.BC_EDGE_RIGHT)
        assert result is None

        # Right boundary should copy from adjacent interior column
        for j in range(ny):
            interior_idx = j * nx + (nx - 2)
            boundary_idx = j * nx + (nx - 1)
            assert (
                field[boundary_idx] == field[interior_idx]
            ), f"Outlet should copy interior at row {j}"

    def test_bc_apply_outlet_velocity_right(self):
        """Test zero-gradient outlet for velocity on right edge"""
        nx, ny = 4, 4
        size = nx * ny
        u = [float(i % nx) for i in range(size)]
        v = [float(i % nx) * 0.5 for i in range(size)]

        result = cfd_python.bc_apply_outlet_velocity(u, v, nx, ny, cfd_python.BC_EDGE_RIGHT)
        assert result is None

        # Right boundary should copy from adjacent interior column
        for j in range(ny):
            interior_idx = j * nx + (nx - 2)
            boundary_idx = j * nx + (nx - 1)
            assert u[boundary_idx] == u[interior_idx], f"u outlet should copy interior at row {j}"
            assert v[boundary_idx] == v[interior_idx], f"v outlet should copy interior at row {j}"


class TestBCFunctionsExported:
    """Test that all BC functions are properly exported"""

    def test_bc_functions_in_all(self):
        """Test all BC functions are in __all__"""
        bc_functions = [
            "bc_get_backend",
            "bc_get_backend_name",
            "bc_set_backend",
            "bc_backend_available",
            "bc_apply_scalar",
            "bc_apply_velocity",
            "bc_apply_dirichlet",
            "bc_apply_noslip",
            "bc_apply_inlet_uniform",
            "bc_apply_inlet_parabolic",
            "bc_apply_outlet_scalar",
            "bc_apply_outlet_velocity",
        ]
        for func_name in bc_functions:
            assert func_name in cfd_python.__all__, f"{func_name} should be in __all__"
            assert callable(getattr(cfd_python, func_name)), f"{func_name} should be callable"

    def test_bc_constants_in_all(self):
        """Test all BC constants are in __all__"""
        bc_constants = [
            # Types
            "BC_TYPE_PERIODIC",
            "BC_TYPE_NEUMANN",
            "BC_TYPE_DIRICHLET",
            "BC_TYPE_NOSLIP",
            "BC_TYPE_INLET",
            "BC_TYPE_OUTLET",
            # Edges
            "BC_EDGE_LEFT",
            "BC_EDGE_RIGHT",
            "BC_EDGE_BOTTOM",
            "BC_EDGE_TOP",
            # Backends
            "BC_BACKEND_AUTO",
            "BC_BACKEND_SCALAR",
            "BC_BACKEND_OMP",
            "BC_BACKEND_SIMD",
            "BC_BACKEND_CUDA",
        ]
        for const_name in bc_constants:
            assert const_name in cfd_python.__all__, f"{const_name} should be in __all__"
