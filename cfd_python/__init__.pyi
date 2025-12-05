"""Type stubs for cfd_python C extension module."""

from typing import Any

__version__: str
__all__: list[str]

# Output type constants
OUTPUT_PRESSURE: int
OUTPUT_VELOCITY: int
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
) -> dict[str, Any]:
    """Create a computational grid.

    Args:
        nx: Grid dimension in x direction
        ny: Grid dimension in y direction
        xmin: Minimum x coordinate
        xmax: Maximum x coordinate
        ymin: Minimum y coordinate
        ymax: Maximum y coordinate

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
    """Get list of all available solver names.

    Returns:
        List of solver name strings
    """
    ...

def has_solver(name: str) -> bool:
    """Check if a solver is available.

    Args:
        name: Solver name to check

    Returns:
        True if solver exists, False otherwise
    """
    ...

def get_solver_info(name: str) -> dict[str, Any]:
    """Get information about a solver.

    Args:
        name: Solver name

    Returns:
        Dictionary with keys:
        - name: str
        - description: str
        - version: str
        - capabilities: list[str]

    Raises:
        ValueError: If solver name is not found
    """
    ...

# Output functions
def set_output_dir(directory: str) -> None:
    """Set the output directory for VTK/CSV files.

    Args:
        directory: Path to output directory
    """
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
) -> None:
    """Write scalar field to VTK file.

    Args:
        filename: Output file path
        field_name: Name of the scalar field
        data: Scalar field data (size nx*ny)
        nx: Grid dimension in x direction
        ny: Grid dimension in y direction
        xmin: Minimum x coordinate
        xmax: Maximum x coordinate
        ymin: Minimum y coordinate
        ymax: Maximum y coordinate

    Raises:
        ValueError: If data size doesn't match nx*ny
    """
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
) -> None:
    """Write vector field to VTK file.

    Args:
        filename: Output file path
        field_name: Name of the vector field
        u_data: U component data (size nx*ny)
        v_data: V component data (size nx*ny)
        nx: Grid dimension in x direction
        ny: Grid dimension in y direction
        xmin: Minimum x coordinate
        xmax: Maximum x coordinate
        ymin: Minimum y coordinate
        ymax: Maximum y coordinate

    Raises:
        ValueError: If data sizes don't match nx*ny
    """
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
    """Write simulation timeseries data to CSV file.

    Args:
        filename: Output file path
        step: Time step number
        time: Simulation time
        u_data: U velocity component (size nx*ny)
        v_data: V velocity component (size nx*ny)
        p_data: Pressure field (size nx*ny)
        nx: Grid dimension in x direction
        ny: Grid dimension in y direction
        dt: Time step size
        iterations: Number of solver iterations
        create_new: If True, create new file; if False, append

    Raises:
        ValueError: If data sizes don't match nx*ny
    """
    ...
