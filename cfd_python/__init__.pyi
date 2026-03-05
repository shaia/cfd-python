"""Type stubs for cfd_python C extension module."""

from typing import Any, Callable

__version__: str
__all__: list[str]

# Status code constants
CFD_SUCCESS: int
CFD_ERROR: int
CFD_ERROR_NOMEM: int
CFD_ERROR_INVALID: int
CFD_ERROR_IO: int
CFD_ERROR_UNSUPPORTED: int
CFD_ERROR_DIVERGED: int
CFD_ERROR_MAX_ITER: int
CFD_ERROR_LIMIT_EXCEEDED: int
CFD_ERROR_NOT_FOUND: int

# Output type constants
OUTPUT_VELOCITY: int
OUTPUT_VELOCITY_MAGNITUDE: int
OUTPUT_FULL_FIELD: int
OUTPUT_CSV_TIMESERIES: int
OUTPUT_CSV_CENTERLINE: int
OUTPUT_CSV_STATISTICS: int

# Dynamic solver constants (generated from C library registry)
# Common solvers - actual availability depends on library build
SOLVER_EXPLICIT_EULER: str
SOLVER_EXPLICIT_EULER_OPTIMIZED: str
SOLVER_PROJECTION: str
SOLVER_PROJECTION_OPTIMIZED: str
SOLVER_EXPLICIT_EULER_GPU: str
SOLVER_PROJECTION_JACOBI_GPU: str

# Version constants (v0.2.0)
CFD_VERSION_MAJOR: int
CFD_VERSION_MINOR: int
CFD_VERSION_PATCH: int

# SIMD architecture constants
SIMD_NONE: int
SIMD_AVX2: int
SIMD_NEON: int

# Solver backend constants
BACKEND_SCALAR: int
BACKEND_SIMD: int
BACKEND_OMP: int
BACKEND_CUDA: int

# Boundary condition type constants
BC_TYPE_PERIODIC: int
BC_TYPE_NEUMANN: int
BC_TYPE_DIRICHLET: int
BC_TYPE_NOSLIP: int
BC_TYPE_INLET: int
BC_TYPE_OUTLET: int
BC_TYPE_SYMMETRY: int

# Boundary condition edge constants
BC_EDGE_LEFT: int
BC_EDGE_RIGHT: int
BC_EDGE_BOTTOM: int
BC_EDGE_TOP: int
BC_EDGE_FRONT: int
BC_EDGE_BACK: int

# Boundary condition backend constants
BC_BACKEND_AUTO: int
BC_BACKEND_SCALAR: int
BC_BACKEND_OMP: int
BC_BACKEND_SIMD: int
BC_BACKEND_CUDA: int

# Poisson solver method constants (v0.2.0)
POISSON_METHOD_JACOBI: int
POISSON_METHOD_GAUSS_SEIDEL: int
POISSON_METHOD_SOR: int
POISSON_METHOD_REDBLACK_SOR: int
POISSON_METHOD_CG: int
POISSON_METHOD_BICGSTAB: int
POISSON_METHOD_MULTIGRID: int

# Poisson solver backend constants (v0.2.0)
POISSON_BACKEND_AUTO: int
POISSON_BACKEND_SCALAR: int
POISSON_BACKEND_OMP: int
POISSON_BACKEND_SIMD: int
POISSON_BACKEND_GPU: int

# Poisson solver type presets (v0.2.0)
POISSON_SOLVER_SOR_SCALAR: int
POISSON_SOLVER_JACOBI_SIMD: int
POISSON_SOLVER_REDBLACK_SIMD: int
POISSON_SOLVER_REDBLACK_OMP: int
POISSON_SOLVER_REDBLACK_SCALAR: int
POISSON_SOLVER_CG_SCALAR: int
POISSON_SOLVER_CG_SIMD: int
POISSON_SOLVER_CG_OMP: int

# Poisson preconditioner constants (v0.2.0)
POISSON_PRECOND_NONE: int
POISSON_PRECOND_JACOBI: int

# Logging constants (v0.2.0)
CFD_LOG_LEVEL_INFO: int
CFD_LOG_LEVEL_WARNING: int
CFD_LOG_LEVEL_ERROR: int

# Simulation functions
def run_simulation(
    nx: int,
    ny: int,
    steps: int = 100,
    xmin: float = 0.0,
    xmax: float = 1.0,
    ymin: float = 0.0,
    ymax: float = 1.0,
    solver_type: str | None = None,
    output_file: str | None = None,
) -> list[float]:
    """Run a complete simulation with default parameters.

    Args:
        nx: Grid dimension in x direction
        ny: Grid dimension in y direction
        steps: Number of time steps (default: 100)
        xmin: Minimum x coordinate (default: 0.0)
        xmax: Maximum x coordinate (default: 1.0)
        ymin: Minimum y coordinate (default: 0.0)
        ymax: Maximum y coordinate (default: 1.0)
        solver_type: Solver name string (optional, uses library default)
        output_file: VTK output file path (optional)

    Returns:
        List of velocity magnitude values (size nx*ny)
    """
    ...

def run_simulation_with_params(
    nx: int,
    ny: int,
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
    steps: int = 1,
    dt: float = 0.001,
    cfl: float = 0.2,
    solver_type: str | None = None,
    output_file: str | None = None,
) -> dict[str, Any]:
    """Run simulation with custom parameters and solver selection.

    Args:
        nx: Grid dimension in x direction
        ny: Grid dimension in y direction
        xmin: Minimum x coordinate
        xmax: Maximum x coordinate
        ymin: Minimum y coordinate
        ymax: Maximum y coordinate
        steps: Number of time steps (default: 1)
        dt: Time step size (default: 0.001)
        cfl: CFL number (default: 0.2)
        solver_type: Solver name string (optional, uses library default)
        output_file: VTK output file path (optional)

    Returns:
        Dictionary with keys:
        - velocity_magnitude: list[float]
        - nx: int
        - ny: int
        - steps: int
        - solver_name: str
        - solver_description: str
        - stats: dict[str, Any]
    """
    ...

def create_grid(
    nx: int,
    ny: int,
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
    nz: int = 1,
    zmin: float = 0.0,
    zmax: float = 0.0,
) -> dict[str, Any]:
    """Create a computational grid.

    Args:
        nx: Grid dimension in x direction
        ny: Grid dimension in y direction
        xmin: Minimum x coordinate
        xmax: Maximum x coordinate
        ymin: Minimum y coordinate
        ymax: Maximum y coordinate
        nz: Grid dimension in z direction (default: 1, 2D grid)
        zmin: Minimum z coordinate (default: 0.0)
        zmax: Maximum z coordinate (default: 0.0)

    Returns:
        Dictionary with keys:
        - nx: int
        - ny: int
        - xmin: float
        - xmax: float
        - ymin: float
        - ymax: float
        - x_coords: list[float]
        - y_coords: list[float]
        - nz: int
        - zmin: float
        - zmax: float
        - z_coords: list[float] (present when nz > 1)
    """
    ...

def create_grid_stretched(
    nx: int,
    ny: int,
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
    beta: float,
) -> dict[str, Any]:
    """Create a computational grid with stretched (non-uniform) spacing.

    Args:
        nx: Grid dimension in x direction
        ny: Grid dimension in y direction
        xmin: Minimum x coordinate
        xmax: Maximum x coordinate
        ymin: Minimum y coordinate
        ymax: Maximum y coordinate
        beta: Stretching parameter (higher = more clustering near boundaries)

    Returns:
        Dictionary with keys:
        - nx: int
        - ny: int
        - xmin: float
        - xmax: float
        - ymin: float
        - ymax: float
        - beta: float
        - x_coords: list[float]
        - y_coords: list[float]
    """
    ...

def get_default_solver_params() -> dict[str, float]:
    """Get default solver parameters.

    Returns:
        Dictionary with keys: dt, cfl, gamma, mu, k, max_iter, tolerance
    """
    ...

# Solver discovery functions
def list_solvers() -> list[str]:
    """Get list of all available solver names."""
    ...

def has_solver(name: str) -> bool:
    """Check if a solver is available."""
    ...

def get_solver_info(name: str) -> dict[str, Any]:
    """Get information about a solver.

    Returns:
        Dictionary with keys: name, description, version, capabilities
    """
    ...

# Output functions
def set_output_dir(directory: str) -> None:
    """Set the output directory for VTK/CSV files (deprecated)."""
    ...

def write_vtk_scalar(
    filename: str,
    field_name: str,
    data: list[float],
    nx: int,
    ny: int,
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
    nz: int = 1,
    zmin: float = 0.0,
    zmax: float = 0.0,
) -> None:
    """Write scalar field to VTK file."""
    ...

def write_vtk_vector(
    filename: str,
    field_name: str,
    u_data: list[float],
    v_data: list[float],
    nx: int,
    ny: int,
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
    w_data: list[float] | None = None,
    nz: int = 1,
    zmin: float = 0.0,
    zmax: float = 0.0,
) -> None:
    """Write vector field to VTK file."""
    ...

def write_csv_timeseries(
    filename: str,
    step: int,
    time: float,
    u_data: list[float],
    v_data: list[float],
    p_data: list[float],
    nx: int,
    ny: int,
    dt: float,
    iterations: int,
    create_new: bool = False,
) -> None:
    """Write simulation timeseries data to CSV file."""
    ...

# Error handling functions
def get_last_error() -> str | None:
    """Get the last CFD error message, or None if no error."""
    ...

def get_last_status() -> int:
    """Get the last CFD status code."""
    ...

def get_error_string(status_code: int) -> str:
    """Get human-readable description for a status code."""
    ...

def clear_error() -> None:
    """Clear the CFD error state."""
    ...

# Boundary condition backend functions
def bc_get_backend() -> int:
    """Get the current boundary condition backend."""
    ...

def bc_get_backend_name() -> str:
    """Get the name of the current boundary condition backend."""
    ...

def bc_set_backend(backend: int) -> bool:
    """Set the boundary condition backend."""
    ...

def bc_backend_available(backend: int) -> bool:
    """Check if a boundary condition backend is available."""
    ...

# Boundary condition application functions
def bc_apply_scalar(field: list[float], nx: int, ny: int, bc_type: int) -> None:
    """Apply boundary conditions to a scalar field (modifies in place)."""
    ...

def bc_apply_velocity(u: list[float], v: list[float], nx: int, ny: int, bc_type: int) -> None:
    """Apply boundary conditions to velocity fields (modifies in place)."""
    ...

def bc_apply_dirichlet(
    field: list[float],
    nx: int,
    ny: int,
    left: float,
    right: float,
    bottom: float,
    top: float,
) -> None:
    """Apply Dirichlet boundary conditions with per-edge values (modifies in place)."""
    ...

def bc_apply_noslip(u: list[float], v: list[float], nx: int, ny: int) -> None:
    """Apply no-slip wall boundary conditions (modifies in place)."""
    ...

def bc_apply_inlet_uniform(
    u: list[float],
    v: list[float],
    nx: int,
    ny: int,
    u_inlet: float,
    v_inlet: float,
    edge: int = ...,
) -> None:
    """Apply uniform inlet boundary conditions (modifies in place)."""
    ...

def bc_apply_inlet_parabolic(
    u: list[float],
    v: list[float],
    nx: int,
    ny: int,
    max_velocity: float,
    edge: int = ...,
) -> None:
    """Apply parabolic inlet boundary conditions (modifies in place)."""
    ...

def bc_apply_outlet_scalar(field: list[float], nx: int, ny: int, edge: int = ...) -> None:
    """Apply zero-gradient outlet BC to scalar field (modifies in place)."""
    ...

def bc_apply_outlet_velocity(
    u: list[float], v: list[float], nx: int, ny: int, edge: int = ...
) -> None:
    """Apply zero-gradient outlet BC to velocity fields (modifies in place)."""
    ...

# Derived fields and statistics
def calculate_field_stats(data: list[float]) -> dict[str, float]:
    """Compute statistics for a field.

    Returns:
        Dictionary with keys: min, max, avg, sum
    """
    ...

def compute_velocity_magnitude(u: list[float], v: list[float], nx: int, ny: int) -> list[float]:
    """Compute velocity magnitude sqrt(u^2 + v^2)."""
    ...

def compute_flow_statistics(
    u: list[float], v: list[float], p: list[float], nx: int, ny: int
) -> dict[str, dict[str, float]]:
    """Compute statistics for all flow field components.

    Returns:
        Dictionary with keys: u, v, p, velocity_magnitude
        Each value is a dict with keys: min, max, avg, sum
    """
    ...

# Solver backend availability functions
def backend_is_available(backend: int) -> bool:
    """Check if a solver backend is available at runtime."""
    ...

def backend_get_name(backend: int) -> str | None:
    """Get human-readable name for a solver backend."""
    ...

def list_solvers_by_backend(backend: int) -> list[str]:
    """Get list of solver names available for a specific backend."""
    ...

def get_available_backends() -> list[str]:
    """Get list of all available backend names."""
    ...

# CPU feature detection functions
def get_simd_arch() -> int:
    """Get the detected SIMD architecture constant."""
    ...

def get_simd_name() -> str:
    """Get the name of the detected SIMD architecture."""
    ...

def has_avx2() -> bool:
    """Check if AVX2 SIMD is available."""
    ...

def has_neon() -> bool:
    """Check if ARM NEON SIMD is available."""
    ...

def has_simd() -> bool:
    """Check if any SIMD (AVX2 or NEON) is available."""
    ...

# Library lifecycle (v0.2.0)
def init() -> None:
    """Initialize the CFD library."""
    ...

def finalize() -> None:
    """Finalize and clean up the CFD library."""
    ...

def is_initialized() -> bool:
    """Check if the CFD library is initialized."""
    ...

def get_cfd_version() -> str:
    """Get the CFD C library version string."""
    ...

# Poisson solver functions (v0.2.0)
def get_default_poisson_params() -> dict[str, Any]:
    """Get default Poisson solver parameters.

    Returns:
        Dictionary with keys: tolerance, absolute_tolerance, max_iterations,
        omega, check_interval, verbose, preconditioner
    """
    ...

def poisson_get_backend() -> int:
    """Get the current Poisson solver backend."""
    ...

def poisson_get_backend_name() -> str:
    """Get the name of the current Poisson solver backend."""
    ...

def poisson_set_backend(backend: int) -> bool:
    """Set the Poisson solver backend."""
    ...

def poisson_backend_available(backend: int) -> bool:
    """Check if a Poisson solver backend is available."""
    ...

def poisson_simd_available() -> bool:
    """Check if SIMD-accelerated Poisson solver is available."""
    ...

# GPU device functions (v0.2.0)
def gpu_is_available() -> bool:
    """Check if GPU acceleration is available."""
    ...

def gpu_get_device_info() -> list[dict[str, Any]]:
    """Get information about available GPU devices."""
    ...

def gpu_select_device(device_id: int) -> None:
    """Select a GPU device by ID."""
    ...

def gpu_get_default_config() -> dict[str, Any]:
    """Get default GPU configuration."""
    ...

# Logging (v0.2.0)
def set_log_callback(callback: Callable[[int, str], None] | None) -> None:
    """Set a Python callback for CFD library log messages.

    Args:
        callback: Function(level: int, message: str), or None to clear.
    """
    ...

# Exception classes
class CFDError(Exception):
    status_code: int
    message: str
    def __init__(self, message: str, status_code: int = -1) -> None: ...

class CFDMemoryError(CFDError, MemoryError): ...
class CFDInvalidError(CFDError, ValueError): ...
class CFDIOError(CFDError, IOError): ...
class CFDUnsupportedError(CFDError, NotImplementedError): ...
class CFDDivergedError(CFDError): ...
class CFDMaxIterError(CFDError): ...
class CFDLimitExceededError(CFDError, ResourceWarning): ...
class CFDNotFoundError(CFDError, LookupError): ...

def raise_for_status(status_code: int, context: str = "") -> None: ...
