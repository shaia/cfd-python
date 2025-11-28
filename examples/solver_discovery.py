#!/usr/bin/env python3
"""
Solver Discovery Example

Demonstrates how to discover and use different solvers dynamically.
Solvers are registered at the C library level and automatically
available in Python.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import cfd_python


def main():
    print("CFD Python - Solver Discovery Example")
    print("=" * 50)

    # List all available solvers
    print("\n1. Listing Available Solvers")
    print("-" * 50)

    solvers = cfd_python.list_solvers()
    print(f"Found {len(solvers)} solver(s):\n")

    for solver_name in solvers:
        print(f"  - {solver_name}")

    # Get detailed info for each solver
    print("\n2. Solver Details")
    print("-" * 50)

    for solver_name in solvers:
        info = cfd_python.get_solver_info(solver_name)
        print(f"\n  {info['name']}:")
        print(f"    Description: {info['description']}")
        print(f"    Version: {info['version']}")
        print(f"    Capabilities: {', '.join(info['capabilities'])}")

    # Check for specific solvers
    print("\n3. Checking for Specific Solvers")
    print("-" * 50)

    solvers_to_check = [
        'explicit_euler',
        'explicit_euler_optimized',
        'projection',
        'explicit_euler_gpu',
        'nonexistent_solver'
    ]

    for name in solvers_to_check:
        available = cfd_python.has_solver(name)
        status = "Available" if available else "Not available"
        print(f"  {name}: {status}")

    # Using dynamic solver constants
    print("\n4. Dynamic Solver Constants")
    print("-" * 50)

    print("  Solver constants are auto-generated from the registry:\n")

    # These constants are dynamically created when the module loads
    if hasattr(cfd_python, 'SOLVER_EXPLICIT_EULER'):
        print(f"  SOLVER_EXPLICIT_EULER = '{cfd_python.SOLVER_EXPLICIT_EULER}'")

    if hasattr(cfd_python, 'SOLVER_EXPLICIT_EULER_OPTIMIZED'):
        print(f"  SOLVER_EXPLICIT_EULER_OPTIMIZED = '{cfd_python.SOLVER_EXPLICIT_EULER_OPTIMIZED}'")

    if hasattr(cfd_python, 'SOLVER_PROJECTION'):
        print(f"  SOLVER_PROJECTION = '{cfd_python.SOLVER_PROJECTION}'")

    # Run simulation with different solvers
    print("\n5. Running Simulations with Different Solvers")
    print("-" * 50)

    for solver_name in solvers[:3]:  # Test first 3 solvers
        print(f"\n  Testing {solver_name}...")
        try:
            result = cfd_python.run_simulation(
                nx=10, ny=10, steps=5,
                solver_type=solver_name
            )
            max_vel = max(result) if result else 0
            print(f"    Success! Max velocity: {max_vel:.6f}")
        except Exception as e:
            print(f"    Error: {e}")

    print("\n" + "=" * 50)
    print("Solver discovery example completed!")


if __name__ == "__main__":
    main()
