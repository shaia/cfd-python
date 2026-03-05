"""CFD Python - Python bindings for CFD simulation library v0.2.0.

This package provides Python bindings for the C-based CFD simulation library,
enabling high-performance computational fluid dynamics simulations from Python.

Solver types are dynamically discovered from the C library. Use list_solvers()
to see all available solvers at runtime. Solver constants (SOLVER_*) are
automatically generated from registered solvers.

Output field types:
    - OUTPUT_VELOCITY_MAGNITUDE: Velocity magnitude scalar field (VTK)
    - OUTPUT_VELOCITY: Velocity vector field (VTK)
    - OUTPUT_FULL_FIELD: Complete flow field (VTK)
    - OUTPUT_CSV_TIMESERIES: Time series data (CSV)
    - OUTPUT_CSV_CENTERLINE: Centerline profile (CSV)
    - OUTPUT_CSV_STATISTICS: Global statistics (CSV)

Error handling:
    - CFD_SUCCESS: Operation successful (0)
    - CFD_ERROR: Generic error (-1)
    - CFD_ERROR_NOMEM: Out of memory (-2)
    - CFD_ERROR_INVALID: Invalid argument (-3)
    - CFD_ERROR_IO: File I/O error (-4)
    - CFD_ERROR_UNSUPPORTED: Operation not supported (-5)
    - CFD_ERROR_DIVERGED: Solver diverged (-6)
    - CFD_ERROR_MAX_ITER: Max iterations reached (-7)
    - CFD_ERROR_LIMIT_EXCEEDED: Resource limit exceeded (-8)
    - CFD_ERROR_NOT_FOUND: Resource not found (-9)
    - get_last_error(): Get last error message
    - get_last_status(): Get last status code
    - get_error_string(code): Get error description
    - clear_error(): Clear error state

Boundary conditions:
    Types:
        - BC_TYPE_PERIODIC: Periodic boundaries
        - BC_TYPE_NEUMANN: Zero-gradient boundaries
        - BC_TYPE_DIRICHLET: Fixed value boundaries
        - BC_TYPE_NOSLIP: No-slip wall (zero velocity)
        - BC_TYPE_INLET: Inlet velocity specification
        - BC_TYPE_OUTLET: Outlet conditions
        - BC_TYPE_SYMMETRY: Symmetry boundary condition

    Edges:
        - BC_EDGE_LEFT, BC_EDGE_RIGHT, BC_EDGE_BOTTOM, BC_EDGE_TOP
        - BC_EDGE_FRONT, BC_EDGE_BACK (3D boundaries)

    Backends:
        - BC_BACKEND_AUTO: Auto-select best available
        - BC_BACKEND_SCALAR: Single-threaded scalar
        - BC_BACKEND_OMP: OpenMP parallel
        - BC_BACKEND_SIMD: SIMD + OpenMP (AVX2/NEON)
        - BC_BACKEND_CUDA: GPU acceleration

    Functions:
        - bc_get_backend(): Get current BC backend
        - bc_get_backend_name(): Get current BC backend name
        - bc_set_backend(backend): Set BC backend
        - bc_backend_available(backend): Check if BC backend is available
        - bc_apply_scalar(field, nx, ny, bc_type): Apply BC to scalar field
        - bc_apply_velocity(u, v, nx, ny, bc_type): Apply BC to velocity
        - bc_apply_dirichlet(field, nx, ny, left, right, bottom, top): Fixed values
        - bc_apply_noslip(u, v, nx, ny): Zero velocity at walls
        - bc_apply_inlet_uniform(u, v, nx, ny, u_inlet, v_inlet, edge): Uniform inlet
        - bc_apply_inlet_parabolic(u, v, nx, ny, max_velocity, edge): Parabolic inlet
        - bc_apply_outlet_scalar(field, nx, ny, edge): Zero-gradient outlet
        - bc_apply_outlet_velocity(u, v, nx, ny, edge): Zero-gradient outlet

Derived fields and statistics:
    - calculate_field_stats(data): Compute min, max, avg, sum for a field
    - compute_velocity_magnitude(u, v, nx, ny): Compute sqrt(u^2 + v^2)
    - compute_flow_statistics(u, v, p, nx, ny): Statistics for all flow components

Solver backend availability (v0.1.6):
    Backends:
        - BACKEND_SCALAR: Basic scalar CPU implementation
        - BACKEND_SIMD: SIMD-optimized (AVX2/SSE)
        - BACKEND_OMP: OpenMP parallelized
        - BACKEND_CUDA: CUDA GPU acceleration

    Functions:
        - backend_is_available(backend): Check if backend is available
        - backend_get_name(backend): Get backend name string
        - list_solvers_by_backend(backend): Get solvers for a backend
        - get_available_backends(): Get list of all available backends

Library lifecycle (v0.2.0):
    - init(): Initialize the CFD library
    - finalize(): Clean up the CFD library
    - is_initialized(): Check if library is initialized
    - get_cfd_version(): Get C library version string

Poisson solver (v0.2.0):
    - get_default_poisson_params(): Default solver parameters
    - poisson_get_backend(): Current backend
    - poisson_get_backend_name(): Current backend name
    - poisson_set_backend(backend): Set backend
    - poisson_backend_available(backend): Check availability
    - poisson_simd_available(): Check SIMD availability

GPU device management (v0.2.0):
    - gpu_is_available(): Check GPU availability
    - gpu_get_device_info(): Get device information
    - gpu_select_device(id): Select a device
    - gpu_get_default_config(): Get default GPU config

Logging (v0.2.0):
    - set_log_callback(callable): Set log callback
"""

from ._exceptions import (
    CFDDivergedError,
    CFDError,
    CFDInvalidError,
    CFDIOError,
    CFDLimitExceededError,
    CFDMaxIterError,
    CFDMemoryError,
    CFDNotFoundError,
    CFDUnsupportedError,
    raise_for_status,
)
from ._version import get_version

__version__ = get_version()

# Core exports list (for documentation and dev mode)
_CORE_EXPORTS = [
    # Simulation functions
    "run_simulation",
    "run_simulation_with_params",
    "create_grid",
    "get_default_solver_params",
    # Solver functions
    "list_solvers",
    "has_solver",
    "get_solver_info",
    # Output functions
    "set_output_dir",
    "write_vtk_scalar",
    "write_vtk_vector",
    "write_csv_timeseries",
    # Output type constants
    "OUTPUT_VELOCITY",
    "OUTPUT_VELOCITY_MAGNITUDE",
    "OUTPUT_FULL_FIELD",
    "OUTPUT_CSV_TIMESERIES",
    "OUTPUT_CSV_CENTERLINE",
    "OUTPUT_CSV_STATISTICS",
    # Error handling API
    "CFD_SUCCESS",
    "CFD_ERROR",
    "CFD_ERROR_NOMEM",
    "CFD_ERROR_INVALID",
    "CFD_ERROR_IO",
    "CFD_ERROR_UNSUPPORTED",
    "CFD_ERROR_DIVERGED",
    "CFD_ERROR_MAX_ITER",
    "get_last_error",
    "get_last_status",
    "get_error_string",
    "clear_error",
    # Boundary condition type constants
    "BC_TYPE_PERIODIC",
    "BC_TYPE_NEUMANN",
    "BC_TYPE_DIRICHLET",
    "BC_TYPE_NOSLIP",
    "BC_TYPE_INLET",
    "BC_TYPE_OUTLET",
    # Boundary edge constants
    "BC_EDGE_LEFT",
    "BC_EDGE_RIGHT",
    "BC_EDGE_BOTTOM",
    "BC_EDGE_TOP",
    # Boundary condition backend constants
    "BC_BACKEND_AUTO",
    "BC_BACKEND_SCALAR",
    "BC_BACKEND_OMP",
    "BC_BACKEND_SIMD",
    "BC_BACKEND_CUDA",
    # Boundary condition functions
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
    # Derived fields API (Phase 3)
    "calculate_field_stats",
    "compute_velocity_magnitude",
    "compute_flow_statistics",
    # Solver backend constants (v0.1.6)
    "BACKEND_SCALAR",
    "BACKEND_SIMD",
    "BACKEND_OMP",
    "BACKEND_CUDA",
    # Solver backend availability functions (v0.1.6)
    "backend_is_available",
    "backend_get_name",
    "list_solvers_by_backend",
    "get_available_backends",
    # Exception classes (Phase 4)
    "CFDError",
    "CFDMemoryError",
    "CFDInvalidError",
    "CFDIOError",
    "CFDUnsupportedError",
    "CFDDivergedError",
    "CFDMaxIterError",
    "raise_for_status",
    # CPU Features API (Phase 6)
    "SIMD_NONE",
    "SIMD_AVX2",
    "SIMD_NEON",
    "get_simd_arch",
    "get_simd_name",
    "has_avx2",
    "has_neon",
    "has_simd",
    # Grid initialization variants (Phase 6)
    "create_grid_stretched",
    # Library lifecycle (v0.2.0)
    "init",
    "finalize",
    "is_initialized",
    "get_cfd_version",
    # Version constants (v0.2.0)
    "CFD_VERSION_MAJOR",
    "CFD_VERSION_MINOR",
    "CFD_VERSION_PATCH",
    # New status codes (v0.2.0)
    "CFD_ERROR_LIMIT_EXCEEDED",
    "CFD_ERROR_NOT_FOUND",
    # New exception classes (v0.2.0)
    "CFDLimitExceededError",
    "CFDNotFoundError",
    # New BC constants (v0.2.0)
    "BC_TYPE_SYMMETRY",
    "BC_EDGE_FRONT",
    "BC_EDGE_BACK",
    # Poisson solver method constants (v0.2.0)
    "POISSON_METHOD_JACOBI",
    "POISSON_METHOD_GAUSS_SEIDEL",
    "POISSON_METHOD_SOR",
    "POISSON_METHOD_REDBLACK_SOR",
    "POISSON_METHOD_CG",
    "POISSON_METHOD_BICGSTAB",
    "POISSON_METHOD_MULTIGRID",
    # Poisson solver backend constants (v0.2.0)
    "POISSON_BACKEND_AUTO",
    "POISSON_BACKEND_SCALAR",
    "POISSON_BACKEND_OMP",
    "POISSON_BACKEND_SIMD",
    "POISSON_BACKEND_GPU",
    # Poisson solver type presets (v0.2.0)
    "POISSON_SOLVER_SOR_SCALAR",
    "POISSON_SOLVER_JACOBI_SIMD",
    "POISSON_SOLVER_REDBLACK_SIMD",
    "POISSON_SOLVER_REDBLACK_OMP",
    "POISSON_SOLVER_REDBLACK_SCALAR",
    "POISSON_SOLVER_CG_SCALAR",
    "POISSON_SOLVER_CG_SIMD",
    "POISSON_SOLVER_CG_OMP",
    # Poisson preconditioner constants (v0.2.0)
    "POISSON_PRECOND_NONE",
    "POISSON_PRECOND_JACOBI",
    # Poisson solver functions (v0.2.0)
    "get_default_poisson_params",
    "poisson_get_backend",
    "poisson_get_backend_name",
    "poisson_set_backend",
    "poisson_backend_available",
    "poisson_simd_available",
    # GPU functions (v0.2.0)
    "gpu_is_available",
    "gpu_get_device_info",
    "gpu_select_device",
    "gpu_get_default_config",
    # Logging (v0.2.0)
    "set_log_callback",
    "CFD_LOG_LEVEL_INFO",
    "CFD_LOG_LEVEL_WARNING",
    "CFD_LOG_LEVEL_ERROR",
]

# Load C extension and populate module namespace
try:
    from ._loader import ExtensionNotBuiltError, load_extension

    _exports, _solver_constants = load_extension()

    # Add all exports to module namespace
    globals().update(_exports)
    globals().update(_solver_constants)

    # Build __all__ with core exports + dynamic solver constants
    __all__ = _CORE_EXPORTS + list(_solver_constants.keys())

except ExtensionNotBuiltError:
    # Development mode - extension not built (this is expected)
    __all__ = _CORE_EXPORTS
