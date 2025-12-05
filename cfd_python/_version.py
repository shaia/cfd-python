"""Version detection for cfd_python package."""

__all__ = ["get_version"]


def get_version() -> str:
    """Get package version from metadata or C module."""
    try:
        from importlib.metadata import PackageNotFoundError, version

        try:
            return version("cfd-python")
        except PackageNotFoundError:
            pass
    except ImportError:
        pass

    # Try C module version
    try:
        from . import cfd_python as _cfd_module

        return getattr(_cfd_module, "__version__", "0.0.0")
    except ImportError:
        pass

    return "0.0.0-dev"
