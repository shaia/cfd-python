"""Version detection for cfd_python package."""

__all__ = ["get_version"]


def get_version() -> str:
    """Get package version from metadata or C module."""
    # Try importlib.metadata first (works when package is installed)
    try:
        from importlib.metadata import PackageNotFoundError, version

        try:
            return version("cfd-python")
        except PackageNotFoundError:
            pass  # Package not installed via pip, try C module next
    except ImportError:
        pass  # Python < 3.8 without importlib_metadata backport

    # Try C module version (works when extension is built)
    try:
        from . import cfd_python as _cfd_module

        return getattr(_cfd_module, "__version__", "0.0.0")
    except ImportError:
        pass  # Extension not built yet (development mode)

    # Fallback for development mode without extension
    return "0.0.0-dev"
