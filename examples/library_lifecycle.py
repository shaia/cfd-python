#!/usr/bin/env python3
"""
Library Lifecycle Example (v0.2.0)

Demonstrates the explicit initialization/finalization API introduced in v0.2.0.
This gives fine-grained control over library resource management and allows
querying version information for compatibility checks.

Key concepts:
- init()/finalize(): Explicit resource management (RAII-style)
- is_initialized(): Guard against double-init or use-before-init
- get_cfd_version(): Runtime version string from the C library
- CFD_VERSION_MAJOR/MINOR/PATCH: Compile-time version constants
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
    print("CFD Python Library Lifecycle Example (v0.2.0)")
    print("=" * 60)

    # =================================================================
    # 1. Version Information
    # =================================================================
    print("\n1. Version Information")
    print("-" * 60)

    print(f"   Python package version: {cfd_python.__version__}")
    print(f"   C library version:      {cfd_python.get_cfd_version()}")
    print(
        f"   Version components:      "
        f"{cfd_python.CFD_VERSION_MAJOR}."
        f"{cfd_python.CFD_VERSION_MINOR}."
        f"{cfd_python.CFD_VERSION_PATCH}"
    )

    # Version compatibility check
    if cfd_python.CFD_VERSION_MINOR >= 2:
        print("   Status: v0.2.0+ features available")
    else:
        print("   Status: Pre-v0.2.0 library detected")

    # =================================================================
    # 2. Initialization State
    # =================================================================
    print("\n2. Initialization State")
    print("-" * 60)

    # Check if already initialized (importing the module may auto-init)
    was_initialized = cfd_python.is_initialized()
    print(f"   Already initialized: {was_initialized}")

    # Explicit initialization - safe to call multiple times
    cfd_python.init()
    print(f"   After init():        {cfd_python.is_initialized()}")

    # =================================================================
    # 3. Using the Library After Init
    # =================================================================
    print("\n3. Using the Library")
    print("-" * 60)

    # All APIs work normally after init
    solvers = cfd_python.list_solvers()
    print(f"   Available solvers: {len(solvers)}")

    grid = cfd_python.create_grid(10, 10, 0.0, 1.0, 0.0, 1.0)
    print(f"   Created grid: {grid['nx']}x{grid['ny']}")

    params = cfd_python.get_default_solver_params()
    print(f"   Default dt: {params['dt']}, CFL: {params['cfl']}")

    # =================================================================
    # 4. Finalization
    # =================================================================
    print("\n4. Finalization")
    print("-" * 60)

    # finalize() releases all library resources
    # After this, API calls may fail until init() is called again
    cfd_python.finalize()
    print(f"   After finalize():    {cfd_python.is_initialized()}")

    # Re-initialize for further use
    cfd_python.init()
    print(f"   After re-init():     {cfd_python.is_initialized()}")

    # =================================================================
    # 5. Context Manager Pattern
    # =================================================================
    print("\n5. Context Manager Pattern (recommended)")
    print("-" * 60)
    print("   For scripts that need explicit lifecycle control,")
    print("   wrap your code in init/finalize:")
    print()
    print("   cfd_python.init()")
    print("   try:")
    print("       # ... your simulation code ...")
    print("   finally:")
    print("       cfd_python.finalize()")

    # =================================================================
    # Summary
    # =================================================================
    print("\n" + "=" * 60)
    print("Summary")
    print("-" * 60)
    print(f"   C library version: {cfd_python.get_cfd_version()}")
    print(f"   Library ready:     {cfd_python.is_initialized()}")
    print("   Lifecycle APIs:    init(), finalize(), is_initialized()")
    print("   Version APIs:      get_cfd_version(), CFD_VERSION_*")


if __name__ == "__main__":
    main()
