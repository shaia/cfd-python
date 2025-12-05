"""CFD Python - Python bindings for CFD simulation library.

This package provides Python bindings for the C-based CFD simulation library,
enabling high-performance computational fluid dynamics simulations from Python.

Solver types are dynamically discovered from the C library. Use list_solvers()
to see all available solvers at runtime. Solver constants (SOLVER_*) are
automatically generated from registered solvers.

Output field types:
    - OUTPUT_PRESSURE: Pressure/velocity magnitude field (VTK)
    - OUTPUT_VELOCITY: Velocity vector field (VTK)
    - OUTPUT_FULL_FIELD: Complete flow field (VTK)
    - OUTPUT_CSV_TIMESERIES: Time series data (CSV)
    - OUTPUT_CSV_CENTERLINE: Centerline profile (CSV)
    - OUTPUT_CSV_STATISTICS: Global statistics (CSV)
"""

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
    "OUTPUT_PRESSURE",
    "OUTPUT_VELOCITY",
    "OUTPUT_FULL_FIELD",
    "OUTPUT_CSV_TIMESERIES",
    "OUTPUT_CSV_CENTERLINE",
    "OUTPUT_CSV_STATISTICS",
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
