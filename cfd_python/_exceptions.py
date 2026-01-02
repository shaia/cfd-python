"""CFD Python exception classes for structured error handling."""

__all__ = [
    "CFDError",
    "CFDMemoryError",
    "CFDInvalidError",
    "CFDIOError",
    "CFDUnsupportedError",
    "CFDDivergedError",
    "CFDMaxIterError",
    "raise_for_status",
]


class CFDError(Exception):
    """Base exception for CFD library errors.

    Attributes:
        status_code: The CFD status code that triggered the error.
        message: Human-readable error message.
    """

    def __init__(self, message: str, status_code: int = -1):
        self.status_code = status_code
        self.message = message
        super().__init__(f"{message} (status={status_code})")


class CFDMemoryError(CFDError, MemoryError):
    """Raised when CFD library fails to allocate memory.

    Corresponds to CFD_ERROR_NOMEM (-2).
    """

    pass


class CFDInvalidError(CFDError, ValueError):
    """Raised when an invalid argument is passed to a CFD function.

    Corresponds to CFD_ERROR_INVALID (-3).
    """

    pass


class CFDIOError(CFDError, IOError):
    """Raised when a file I/O operation fails.

    Corresponds to CFD_ERROR_IO (-4).
    """

    pass


class CFDUnsupportedError(CFDError, NotImplementedError):
    """Raised when an unsupported operation is requested.

    Corresponds to CFD_ERROR_UNSUPPORTED (-5).
    This typically occurs when requesting a backend that is not available.
    """

    pass


class CFDDivergedError(CFDError):
    """Raised when the solver diverges during computation.

    Corresponds to CFD_ERROR_DIVERGED (-6).
    This indicates numerical instability, often due to time step being too large.
    """

    pass


class CFDMaxIterError(CFDError):
    """Raised when solver reaches maximum iteration limit without converging.

    Corresponds to CFD_ERROR_MAX_ITER (-7).
    Consider increasing max_iter or adjusting solver parameters.
    """

    pass


# Mapping from status codes to exception classes
_STATUS_TO_EXCEPTION = {
    -1: CFDError,  # CFD_ERROR (generic)
    -2: CFDMemoryError,  # CFD_ERROR_NOMEM
    -3: CFDInvalidError,  # CFD_ERROR_INVALID
    -4: CFDIOError,  # CFD_ERROR_IO
    -5: CFDUnsupportedError,  # CFD_ERROR_UNSUPPORTED
    -6: CFDDivergedError,  # CFD_ERROR_DIVERGED
    -7: CFDMaxIterError,  # CFD_ERROR_MAX_ITER
}


def raise_for_status(status_code: int, context: str = "") -> None:
    """Raise an appropriate exception if status_code indicates an error.

    Args:
        status_code: The CFD status code to check.
        context: Optional context string to include in the error message.

    Raises:
        CFDError: Or an appropriate subclass based on the status code.

    Example:
        >>> status = some_cfd_operation()
        >>> raise_for_status(status, "during simulation step")
    """
    if status_code >= 0:
        return  # Success

    # Try to get error message from CFD library
    try:
        from . import get_error_string, get_last_error

        error_msg = get_last_error()
        if not error_msg:
            error_msg = get_error_string(status_code)
    except (ImportError, AttributeError):
        error_msg = f"CFD error code {status_code}"

    if context:
        error_msg = f"{context}: {error_msg}"

    exception_class = _STATUS_TO_EXCEPTION.get(status_code, CFDError)
    raise exception_class(error_msg, status_code)
