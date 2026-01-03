#!/usr/bin/env python3
"""
Error Handling Example

This example demonstrates the error handling API in cfd_python,
including exception classes and the raise_for_status helper.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import cfd_python
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure to build the package first:")
    print("  pip install -e .")
    sys.exit(1)


def main():
    print("CFD Python Error Handling Example")
    print("=" * 60)

    # =================================================================
    # 1. Error Status Constants
    # =================================================================
    print("\n1. Error Status Constants")
    print("-" * 60)

    error_codes = [
        ("CFD_SUCCESS", cfd_python.CFD_SUCCESS),
        ("CFD_ERROR", cfd_python.CFD_ERROR),
        ("CFD_ERROR_NOMEM", cfd_python.CFD_ERROR_NOMEM),
        ("CFD_ERROR_INVALID", cfd_python.CFD_ERROR_INVALID),
        ("CFD_ERROR_IO", cfd_python.CFD_ERROR_IO),
        ("CFD_ERROR_UNSUPPORTED", cfd_python.CFD_ERROR_UNSUPPORTED),
        ("CFD_ERROR_DIVERGED", cfd_python.CFD_ERROR_DIVERGED),
        ("CFD_ERROR_MAX_ITER", cfd_python.CFD_ERROR_MAX_ITER),
    ]

    print("   Status codes defined:")
    for name, value in error_codes:
        desc = cfd_python.get_error_string(value)
        print(f"     {name} = {value}: {desc}")

    # =================================================================
    # 2. Checking Error State
    # =================================================================
    print("\n2. Checking Error State")
    print("-" * 60)

    # Clear any existing error
    cfd_python.clear_error()
    print("   Cleared error state")

    # Check current status
    status = cfd_python.get_last_status()
    error_msg = cfd_python.get_last_error()

    print(f"   Current status: {status}")
    print(f"   Error message: {error_msg if error_msg else '(none)'}")

    # Demonstrate error checking pattern
    if status == cfd_python.CFD_SUCCESS:
        print("   Status is OK - no errors")
    else:
        print(f"   Error occurred: {cfd_python.get_error_string(status)}")

    # =================================================================
    # 3. Exception Classes
    # =================================================================
    print("\n3. Exception Classes")
    print("-" * 60)

    exceptions = [
        ("CFDError", cfd_python.CFDError, Exception),
        ("CFDMemoryError", cfd_python.CFDMemoryError, MemoryError),
        ("CFDInvalidError", cfd_python.CFDInvalidError, ValueError),
        ("CFDIOError", cfd_python.CFDIOError, OSError),
        ("CFDUnsupportedError", cfd_python.CFDUnsupportedError, NotImplementedError),
        ("CFDDivergedError", cfd_python.CFDDivergedError, cfd_python.CFDError),
        ("CFDMaxIterError", cfd_python.CFDMaxIterError, cfd_python.CFDError),
    ]

    print("   Exception hierarchy (showing Method Resolution Order):")
    for name, exc_class, _ in exceptions:
        # Filter MRO to show base classes, excluding the class itself and 'object'
        bases = ", ".join(b.__name__ for b in exc_class.__mro__ if b not in (exc_class, object))
        print(f"     {name} <- {bases}")

    # =================================================================
    # 4. Using raise_for_status
    # =================================================================
    print("\n4. Using raise_for_status")
    print("-" * 60)

    # Test with success
    try:
        cfd_python.raise_for_status(cfd_python.CFD_SUCCESS, context="test operation")
        print("   CFD_SUCCESS: No exception raised (as expected)")
    except cfd_python.CFDError as e:
        print(f"   Unexpected error: {e}")

    # Test with each error code
    test_codes = [
        (cfd_python.CFD_ERROR, "generic operation"),
        (cfd_python.CFD_ERROR_NOMEM, "allocation"),
        (cfd_python.CFD_ERROR_INVALID, "parameter validation"),
        (cfd_python.CFD_ERROR_IO, "file writing"),
        (cfd_python.CFD_ERROR_UNSUPPORTED, "feature check"),
        (cfd_python.CFD_ERROR_DIVERGED, "solver step"),
        (cfd_python.CFD_ERROR_MAX_ITER, "convergence"),
    ]

    print("\n   Testing raise_for_status with error codes:")
    for code, context in test_codes:
        try:
            cfd_python.raise_for_status(code, context=context)
        except cfd_python.CFDMemoryError as e:
            print(f"     {code}: CFDMemoryError - {e}")
        except cfd_python.CFDInvalidError as e:
            print(f"     {code}: CFDInvalidError - {e}")
        except cfd_python.CFDIOError as e:
            print(f"     {code}: CFDIOError - {e}")
        except cfd_python.CFDUnsupportedError as e:
            print(f"     {code}: CFDUnsupportedError - {e}")
        except cfd_python.CFDDivergedError as e:
            print(f"     {code}: CFDDivergedError - {e}")
        except cfd_python.CFDMaxIterError as e:
            print(f"     {code}: CFDMaxIterError - {e}")
        except cfd_python.CFDError as e:
            print(f"     {code}: CFDError - {e}")

    # =================================================================
    # 5. Practical Error Handling Pattern
    # =================================================================
    print("\n5. Practical Error Handling Pattern")
    print("-" * 60)

    def safe_simulation(nx, ny, steps):
        """Run simulation with proper error handling."""
        try:
            # Clear any previous errors
            cfd_python.clear_error()

            # Run simulation
            result = cfd_python.run_simulation_with_params(
                nx=nx, ny=ny, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0, steps=steps, dt=0.001
            )

            # Check for errors
            status = cfd_python.get_last_status()
            if status != cfd_python.CFD_SUCCESS:
                cfd_python.raise_for_status(status, context="simulation")

            return result

        except cfd_python.CFDDivergedError:
            print("     Solver diverged - try smaller time step")
            return None
        except cfd_python.CFDMaxIterError:
            print("     Max iterations reached - may need more steps")
            return None
        except cfd_python.CFDInvalidError as e:
            print(f"     Invalid parameters: {e}")
            return None
        except cfd_python.CFDError as e:
            print(f"     CFD error: {e}")
            return None

    print("   Running safe_simulation(32, 32, 10)...")
    result = safe_simulation(32, 32, 10)
    if result:
        print(f"     Success! Got {len(result['velocity_magnitude'])} values")

    # =================================================================
    # 6. Handling Specific Errors
    # =================================================================
    print("\n6. Handling Specific Errors")
    print("-" * 60)

    # Use Python's standard exception handling
    print("   CFD exceptions inherit from Python built-ins:")

    # CFDMemoryError can be caught as MemoryError
    try:
        raise cfd_python.CFDMemoryError("Out of memory during grid allocation", -2)
    except MemoryError as e:
        print(f"     Caught as MemoryError: {e}")

    # CFDInvalidError can be caught as ValueError
    try:
        raise cfd_python.CFDInvalidError("Invalid grid dimensions", -3)
    except ValueError as e:
        print(f"     Caught as ValueError: {e}")

    # CFDIOError can be caught as OSError (IOError is an alias in Python 3)
    try:
        raise cfd_python.CFDIOError("Cannot write to output file", -4)
    except OSError as e:
        print(f"     Caught as OSError: {e}")

    # =================================================================
    # Summary
    # =================================================================
    print("\n" + "=" * 60)
    print("Error Handling Best Practices:")
    print("  1. Use cfd_python.clear_error() before critical operations")
    print("  2. Check cfd_python.get_last_status() after operations")
    print("  3. Use raise_for_status() for automatic exception raising")
    print("  4. Catch specific exceptions (CFDDivergedError, etc.)")
    print("  5. CFD exceptions inherit from Python built-ins for compatibility")


if __name__ == "__main__":
    main()
