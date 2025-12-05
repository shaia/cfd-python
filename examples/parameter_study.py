#!/usr/bin/env python3
"""
Parameter Study Example

Demonstrates how to run multiple simulations with varying parameters
to study the effect of different settings on the solution.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

import cfd_python


def run_grid_convergence_study():
    """Study the effect of grid resolution on the solution."""
    print("\n1. Grid Convergence Study")
    print("-" * 50)

    grid_sizes = [8, 16, 32, 64]
    results = []

    for n in grid_sizes:
        result = cfd_python.run_simulation(
            nx=n, ny=n, steps=20, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0
        )
        vel_array = np.array(result)
        max_vel = np.max(vel_array)
        avg_vel = np.mean(vel_array)
        results.append((n, max_vel, avg_vel))
        print(f"   Grid {n}x{n}: max_vel={max_vel:.6f}, avg_vel={avg_vel:.6f}")

    return results


def run_timestep_study():
    """Study the effect of time step size on stability and accuracy."""
    print("\n2. Time Step Study")
    print("-" * 50)

    nx, ny = 20, 20
    dt_values = [0.01, 0.005, 0.001, 0.0005]
    results = []

    for dt in dt_values:
        try:
            result = cfd_python.run_simulation_with_params(
                nx=nx, ny=ny, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0, steps=10, dt=dt, cfl=0.5
            )
            vel_mag = result.get("velocity_magnitude", [])
            max_vel = max(vel_mag) if vel_mag else 0
            status = "OK"
        except Exception as e:
            max_vel = float("nan")
            status = f"Failed: {e}"

        results.append((dt, max_vel, status))
        print(f"   dt={dt}: max_vel={max_vel:.6f} [{status}]")

    return results


def run_solver_comparison():
    """Compare different solvers on the same problem."""
    print("\n3. Solver Comparison")
    print("-" * 50)

    nx, ny = 20, 20
    steps = 20
    solvers = cfd_python.list_solvers()
    results = []

    for solver_name in solvers:
        try:
            result = cfd_python.run_simulation(nx=nx, ny=ny, steps=steps, solver_type=solver_name)
            vel_array = np.array(result)
            max_vel = np.max(vel_array)
            avg_vel = np.mean(vel_array)
            status = "OK"
        except Exception:
            max_vel = avg_vel = float("nan")
            status = "Failed"

        results.append((solver_name, max_vel, avg_vel, status))
        print(f"   {solver_name:30s}: max={max_vel:.6f}, avg={avg_vel:.6f} [{status}]")

    return results


def run_domain_size_study():
    """Study the effect of domain size on the solution."""
    print("\n4. Domain Size Study")
    print("-" * 50)

    nx, ny = 20, 20
    domain_sizes = [
        (1.0, 1.0),
        (2.0, 1.0),
        (1.0, 2.0),
        (2.0, 2.0),
    ]
    results = []

    for xsize, ysize in domain_sizes:
        result = cfd_python.run_simulation(
            nx=nx, ny=ny, steps=20, xmin=0.0, xmax=xsize, ymin=0.0, ymax=ysize
        )
        vel_array = np.array(result)
        max_vel = np.max(vel_array)

        results.append((xsize, ysize, max_vel))
        print(f"   Domain [{xsize}x{ysize}]: max_vel={max_vel:.6f}")

    return results


def main():
    print("CFD Python - Parameter Study Example")
    print("=" * 50)

    # Run all studies
    grid_results = run_grid_convergence_study()
    timestep_results = run_timestep_study()
    solver_results = run_solver_comparison()
    domain_results = run_domain_size_study()

    # Summary
    print("\n" + "=" * 50)
    print("Parameter Study Summary")
    print("=" * 50)

    print("\nGrid Convergence:")
    for n, max_vel, avg_vel in grid_results:
        print(f"  {n:3d}x{n:<3d}: max={max_vel:.6f}")

    print("\nTime Step Study:")
    for dt, max_vel, status in timestep_results:
        print(f"  dt={dt}: max={max_vel:.6f} [{status}]")

    print("\nBest performing solver:")
    valid_solvers = [(name, max_v) for name, max_v, _, status in solver_results if status == "OK"]
    if valid_solvers:
        best = max(valid_solvers, key=lambda x: x[1])
        print(f"  {best[0]} (max_vel={best[1]:.6f})")

    print("\nDomain Size Study:")
    for xsize, ysize, max_vel in domain_results:
        print(f"  [{xsize}x{ysize}]: max={max_vel:.6f}")

    print("\nStudy completed!")


if __name__ == "__main__":
    main()
