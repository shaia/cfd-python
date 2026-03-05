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

    Auto-discovers all public symbols from the C extension via dir().
    SOLVER_* constants are returned separately since they are dynamically
    generated from the solver registry at import time.

    Returns:
        tuple: (exports_dict, solver_constants)

    Raises:
        ImportError: If extension exists but fails to load
        ExtensionNotBuiltError: If extension is not built (dev mode)
    """
    try:
        from . import cfd_python as _cfd_module

        # Auto-collect all public symbols from the C extension
        exports = {}
        for name in dir(_cfd_module):
            if not name.startswith("_"):
                exports[name] = getattr(_cfd_module, name)

        # Separate SOLVER_* constants (dynamically generated from registry)
        solver_constants = {k: v for k, v in exports.items() if k.startswith("SOLVER_")}
        for k in solver_constants:
            del exports[k]

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
