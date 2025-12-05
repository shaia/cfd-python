#!/usr/bin/env python3
"""
Basic CFD Python Example

This example demonstrates the fundamental usage of the CFD Python bindings
for running fluid dynamics simulations.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import numpy as np

    import cfd_python
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure to build the package first:")
    print("  pip install -e .")
    sys.exit(1)


def main():
    print("CFD Python Basic Example")
    print("=" * 50)
    print(f"Version: {cfd_python.__version__}")

    # Show available solvers
    print("\nAvailable Solvers:")
    for solver in cfd_python.list_solvers():
        print(f"  - {solver}")

    # Simulation parameters
    nx, ny = 20, 20
    xmin, xmax = 0.0, 1.0
    ymin, ymax = 0.0, 1.0
    steps = 50

    print("\nSimulation Setup:")
    print(f"  Grid: {nx} x {ny}")
    print(f"  Domain: [{xmin}, {xmax}] x [{ymin}, {ymax}]")
    print(f"  Steps: {steps}")

    # Method 1: Simple simulation
    print("\n" + "-" * 50)
    print("1. Simple Simulation (run_simulation)")
    print("-" * 50)

    vel_mag = cfd_python.run_simulation(
        nx=nx, ny=ny, steps=steps, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax
    )

    vel_array = np.array(vel_mag)
    print(f"   Completed: {len(vel_mag)} points")
    print(f"   Max velocity: {np.max(vel_array):.6f}")
    print(f"   Mean velocity: {np.mean(vel_array):.6f}")

    # Method 2: With VTK output
    print("\n" + "-" * 50)
    print("2. Simulation with VTK Output")
    print("-" * 50)

    vel_mag_vtk = cfd_python.run_simulation(
        nx=nx, ny=ny, steps=steps, output_file="basic_output.vtk"
    )
    print(f"   Output: basic_output.vtk ({len(vel_mag_vtk)} points)")

    # Method 3: Using run_simulation_with_params
    print("\n" + "-" * 50)
    print("3. Custom Parameters (run_simulation_with_params)")
    print("-" * 50)

    result = cfd_python.run_simulation_with_params(
        nx=nx, ny=ny, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax, steps=25, dt=0.0005, cfl=0.2
    )

    print(f"   Grid: {result['nx']} x {result['ny']}")
    if "stats" in result:
        stats = result["stats"]
        print(f"   Max velocity: {stats.get('max_velocity', 'N/A')}")
        print(f"   Iterations: {stats.get('iterations', 'N/A')}")

    # Method 4: Grid and parameter inspection
    print("\n" + "-" * 50)
    print("4. Grid and Parameter Inspection")
    print("-" * 50)

    grid = cfd_python.create_grid(nx, ny, xmin, xmax, ymin, ymax)
    print(f"   Grid dimensions: {grid['nx']} x {grid['ny']}")
    print(f"   X coordinates: {len(grid['x_coords'])} points")

    params = cfd_python.get_default_solver_params()
    print(f"   Default dt: {params['dt']}")
    print(f"   Default CFL: {params['cfl']}")

    # Summary
    print("\n" + "=" * 50)
    print("Example completed!")
    print("\nAvailable functions:")
    print("  - run_simulation(): Quick simulation")
    print("  - run_simulation_with_params(): Custom parameters")
    print("  - create_grid(): Create computational grid")
    print("  - get_default_solver_params(): Get default settings")
    print("  - list_solvers(): List available solvers")
    print("  - write_vtk_scalar/vector(): Export to VTK")
    print("  - write_csv_timeseries(): Export to CSV")


if __name__ == "__main__":
    main()
