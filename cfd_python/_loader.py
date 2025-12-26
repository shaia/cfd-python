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
        from . import cfd_python as _cfd_module
        from .cfd_python import (
            # Boundary condition backends
            BC_BACKEND_AUTO,
            BC_BACKEND_CUDA,
            BC_BACKEND_OMP,
            BC_BACKEND_SCALAR,
            BC_BACKEND_SIMD,
            BC_EDGE_BOTTOM,
            # Boundary edges
            BC_EDGE_LEFT,
            BC_EDGE_RIGHT,
            BC_EDGE_TOP,
            BC_TYPE_DIRICHLET,
            BC_TYPE_INLET,
            BC_TYPE_NEUMANN,
            BC_TYPE_NOSLIP,
            BC_TYPE_OUTLET,
            # Boundary condition types
            BC_TYPE_PERIODIC,
            CFD_ERROR,
            CFD_ERROR_DIVERGED,
            CFD_ERROR_INVALID,
            CFD_ERROR_IO,
            CFD_ERROR_MAX_ITER,
            CFD_ERROR_NOMEM,
            CFD_ERROR_UNSUPPORTED,
            # Error handling API
            CFD_SUCCESS,
            OUTPUT_CSV_CENTERLINE,
            OUTPUT_CSV_STATISTICS,
            OUTPUT_CSV_TIMESERIES,
            OUTPUT_FULL_FIELD,
            OUTPUT_VELOCITY,
            OUTPUT_VELOCITY_MAGNITUDE,
            bc_apply_dirichlet,
            bc_apply_inlet_parabolic,
            bc_apply_inlet_uniform,
            bc_apply_noslip,
            bc_apply_outlet_scalar,
            bc_apply_outlet_velocity,
            bc_apply_scalar,
            bc_apply_velocity,
            bc_backend_available,
            # Boundary condition functions
            bc_get_backend,
            bc_get_backend_name,
            bc_set_backend,
            clear_error,
            # Core functions
            create_grid,
            get_default_solver_params,
            get_error_string,
            get_last_error,
            get_last_status,
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
            "OUTPUT_VELOCITY": OUTPUT_VELOCITY,
            "OUTPUT_VELOCITY_MAGNITUDE": OUTPUT_VELOCITY_MAGNITUDE,
            "OUTPUT_FULL_FIELD": OUTPUT_FULL_FIELD,
            "OUTPUT_CSV_TIMESERIES": OUTPUT_CSV_TIMESERIES,
            "OUTPUT_CSV_CENTERLINE": OUTPUT_CSV_CENTERLINE,
            "OUTPUT_CSV_STATISTICS": OUTPUT_CSV_STATISTICS,
            # Error handling API
            "CFD_SUCCESS": CFD_SUCCESS,
            "CFD_ERROR": CFD_ERROR,
            "CFD_ERROR_NOMEM": CFD_ERROR_NOMEM,
            "CFD_ERROR_INVALID": CFD_ERROR_INVALID,
            "CFD_ERROR_IO": CFD_ERROR_IO,
            "CFD_ERROR_UNSUPPORTED": CFD_ERROR_UNSUPPORTED,
            "CFD_ERROR_DIVERGED": CFD_ERROR_DIVERGED,
            "CFD_ERROR_MAX_ITER": CFD_ERROR_MAX_ITER,
            "get_last_error": get_last_error,
            "get_last_status": get_last_status,
            "get_error_string": get_error_string,
            "clear_error": clear_error,
            # Boundary condition type constants
            "BC_TYPE_PERIODIC": BC_TYPE_PERIODIC,
            "BC_TYPE_NEUMANN": BC_TYPE_NEUMANN,
            "BC_TYPE_DIRICHLET": BC_TYPE_DIRICHLET,
            "BC_TYPE_NOSLIP": BC_TYPE_NOSLIP,
            "BC_TYPE_INLET": BC_TYPE_INLET,
            "BC_TYPE_OUTLET": BC_TYPE_OUTLET,
            # Boundary edge constants
            "BC_EDGE_LEFT": BC_EDGE_LEFT,
            "BC_EDGE_RIGHT": BC_EDGE_RIGHT,
            "BC_EDGE_BOTTOM": BC_EDGE_BOTTOM,
            "BC_EDGE_TOP": BC_EDGE_TOP,
            # Boundary condition backend constants
            "BC_BACKEND_AUTO": BC_BACKEND_AUTO,
            "BC_BACKEND_SCALAR": BC_BACKEND_SCALAR,
            "BC_BACKEND_OMP": BC_BACKEND_OMP,
            "BC_BACKEND_SIMD": BC_BACKEND_SIMD,
            "BC_BACKEND_CUDA": BC_BACKEND_CUDA,
            # Boundary condition functions
            "bc_get_backend": bc_get_backend,
            "bc_get_backend_name": bc_get_backend_name,
            "bc_set_backend": bc_set_backend,
            "bc_backend_available": bc_backend_available,
            "bc_apply_scalar": bc_apply_scalar,
            "bc_apply_velocity": bc_apply_velocity,
            "bc_apply_dirichlet": bc_apply_dirichlet,
            "bc_apply_noslip": bc_apply_noslip,
            "bc_apply_inlet_uniform": bc_apply_inlet_uniform,
            "bc_apply_inlet_parabolic": bc_apply_inlet_parabolic,
            "bc_apply_outlet_scalar": bc_apply_outlet_scalar,
            "bc_apply_outlet_velocity": bc_apply_outlet_velocity,
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
