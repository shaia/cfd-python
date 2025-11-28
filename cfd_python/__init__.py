"""CFD Python - Python bindings for CFD simulation library

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

# Get version from package metadata (setuptools-scm) or fall back to C module
try:
    from importlib.metadata import version, PackageNotFoundError
    try:
        __version__ = version("cfd-python")
    except PackageNotFoundError:
        # Package not installed, try C module version
        __version__ = None
except ImportError:
    # Fallback for unusual environments where importlib.metadata is unavailable
    __version__ = None

# Core exports that are always available
_CORE_EXPORTS = [
    # Simulation functions
    "run_simulation",
    "create_grid",
    "get_default_solver_params",
    "run_simulation_with_params",
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

try:
    from .cfd_python import (
        # Simulation functions
        run_simulation,
        create_grid,
        get_default_solver_params,
        run_simulation_with_params,
        # Solver functions
        list_solvers,
        has_solver,
        get_solver_info,
        # Output functions
        set_output_dir,
        write_vtk_scalar,
        write_vtk_vector,
        write_csv_timeseries,
        # Output type constants
        OUTPUT_PRESSURE,
        OUTPUT_VELOCITY,
        OUTPUT_FULL_FIELD,
        OUTPUT_CSV_TIMESERIES,
        OUTPUT_CSV_CENTERLINE,
        OUTPUT_CSV_STATISTICS,
    )

    # Import the C extension module to access dynamic solver constants
    from . import cfd_python as _cfd_module

    # Fall back to C module version if metadata lookup failed
    if __version__ is None:
        __version__ = getattr(_cfd_module, '__version__', '0.0.0')

    # Dynamically export all SOLVER_* constants from the C module
    # This allows new solvers to be automatically available without
    # updating this file
    _solver_constants = []
    for name in dir(_cfd_module):
        if name.startswith("SOLVER_"):
            globals()[name] = getattr(_cfd_module, name)
            _solver_constants.append(name)

    # Build complete __all__ list
    __all__ = _CORE_EXPORTS + _solver_constants

except ImportError:
    # Development mode - module not yet built
    __all__ = _CORE_EXPORTS
    if __version__ is None:
        __version__ = "0.0.0-dev"