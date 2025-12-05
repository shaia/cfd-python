"""C extension loader with error handling for cfd_python."""

import os

__all__ = ["load_extension", "ExtensionNotBuiltError"]


class ExtensionNotBuiltError(ImportError):
    """Raised when C extension is not built (development mode)."""

    pass


def _check_extension_exists() -> bool:
    """Check if compiled extension files exist in package directory."""
    package_dir = os.path.dirname(__file__)
    return any(
        f.startswith("cfd_python") and (f.endswith(".pyd") or f.endswith(".so"))
        for f in os.listdir(package_dir)
    )


def load_extension():
    """Load the C extension module and return exports.

    Returns:
        tuple: (exports_dict, solver_constants)

    Raises:
        ImportError: If extension exists but fails to load
        ExtensionNotBuiltError: If extension is not built (dev mode)
    """
    try:
        from . import cfd_python as _cfd_module  # noqa: F401
        from .cfd_python import (
            OUTPUT_CSV_CENTERLINE,
            OUTPUT_CSV_STATISTICS,
            OUTPUT_CSV_TIMESERIES,
            OUTPUT_FULL_FIELD,
            OUTPUT_PRESSURE,
            OUTPUT_VELOCITY,
            create_grid,
            get_default_solver_params,
            get_solver_info,
            has_solver,
            list_solvers,
            run_simulation,
            run_simulation_with_params,
            set_output_dir,
            write_csv_timeseries,
            write_vtk_scalar,
            write_vtk_vector,
        )

        # Collect all exports
        exports = {
            # Simulation functions
            "run_simulation": run_simulation,
            "run_simulation_with_params": run_simulation_with_params,
            "create_grid": create_grid,
            "get_default_solver_params": get_default_solver_params,
            # Solver functions
            "list_solvers": list_solvers,
            "has_solver": has_solver,
            "get_solver_info": get_solver_info,
            # Output functions
            "set_output_dir": set_output_dir,
            "write_vtk_scalar": write_vtk_scalar,
            "write_vtk_vector": write_vtk_vector,
            "write_csv_timeseries": write_csv_timeseries,
            # Output type constants
            "OUTPUT_PRESSURE": OUTPUT_PRESSURE,
            "OUTPUT_VELOCITY": OUTPUT_VELOCITY,
            "OUTPUT_FULL_FIELD": OUTPUT_FULL_FIELD,
            "OUTPUT_CSV_TIMESERIES": OUTPUT_CSV_TIMESERIES,
            "OUTPUT_CSV_CENTERLINE": OUTPUT_CSV_CENTERLINE,
            "OUTPUT_CSV_STATISTICS": OUTPUT_CSV_STATISTICS,
        }

        # Collect dynamic SOLVER_* constants
        solver_constants = {}
        for name in dir(_cfd_module):
            if name.startswith("SOLVER_"):
                solver_constants[name] = getattr(_cfd_module, name)

        return exports, solver_constants

    except ImportError as e:
        if _check_extension_exists():
            # Extension file exists but failed to load - this is an error
            raise ImportError(
                f"Failed to load cfd_python C extension: {e}\n"
                "The extension file exists but could not be imported. "
                "This may indicate a missing dependency or ABI incompatibility."
            ) from e
        else:
            # Development mode - module not yet built
            raise ExtensionNotBuiltError(
                "C extension not built. Run 'pip install -e .' to build."
            ) from e
