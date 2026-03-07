#!/usr/bin/env python3
"""
Heat Conduction Example

This example demonstrates steady-state 2D heat conduction on a unit square
plate using Dirichlet boundary conditions and a Jacobi iterative solver.

Physics Background:
-------------------
Steady-state heat conduction is governed by the Laplace equation:

    ∇²T = 0  →  ∂²T/∂x² + ∂²T/∂y² = 0

This is the limit of the transient heat equation ∂T/∂t = α∇²T as t → ∞,
where thermal diffusivity α drops out and the solution depends only on the
boundary conditions.

Boundary conditions (Dirichlet - fixed temperature):
   - Left wall:   T = 100 degC  (hot source)
   - Right wall:  T =   0 degC  (cold sink)
   - Top wall:    T =  50 degC  (warm boundary)
   - Bottom wall: T =   0 degC  (cold boundary)

Numerical method - Jacobi iteration:
Each interior node is updated as the average of its four neighbours:

    T_new[i,j] = 0.25 * (T[i-1,j] + T[i+1,j] + T[i,j-1] + T[i,j+1])

This is the finite-difference discretisation of ∇²T = 0 on a uniform grid.
The scheme converges when the maximum change between successive iterations
falls below the specified tolerance.

Expected behaviour:
   - The interior temperature field must satisfy 0 ≤ T ≤ 100.
   - Heat flows from the hot left boundary toward the cold right boundary.
   - The centre-point temperature should lie between 0 degC and 100 degC, biased
     toward the average of the four boundary values (~37.5 degC).
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

import numpy as np


def main():
    print("CFD Python - Heat Conduction Example")
    print("=" * 60)

    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Problem Setup
    # ------------------------------------------------------------------
    nx, ny = 32, 32
    xmin, xmax = 0.0, 1.0
    ymin, ymax = 0.0, 1.0

    # Boundary temperatures ( degC)
    T_left = 100.0
    T_right = 0.0
    T_top = 50.0
    T_bottom = 0.0

    # Solver parameters
    max_iterations = 10_000
    tolerance = 1e-5

    print("\nProblem Setup:")
    print(f"  Grid:              {nx} x {ny}")
    print(f"  Domain:            [{xmin}, {xmax}] x [{ymin}, {ymax}]")
    print(f"  Left wall (hot):   T = {T_left:.1f} degC")
    print(f"  Right wall (cold): T = {T_right:.1f} degC")
    print(f"  Top wall:          T = {T_top:.1f} degC")
    print(f"  Bottom wall:       T = {T_bottom:.1f} degC")
    print(f"  Max iterations:    {max_iterations}")
    print(f"  Tolerance:         {tolerance}")

    # Create the computational grid via the library API
    _ = cfd_python.create_grid(nx, ny, xmin, xmax, ymin, ymax)
    dx = (xmax - xmin) / (nx - 1)
    dy = (ymax - ymin) / (ny - 1)
    print(f"\nGrid created - dx = {dx:.6f}, dy = {dy:.6f}")

    # ------------------------------------------------------------------
    # Simulation - Jacobi iterative solver
    # ------------------------------------------------------------------
    print("\nRunning Jacobi iterations...")

    # Initialise temperature field (flat list, row-major: index = j*nx + i)
    T = [0.0] * (nx * ny)

    # Apply Dirichlet boundary conditions through the library API.
    # bc_apply_dirichlet sets the four edges to the prescribed values.
    cfd_python.bc_apply_dirichlet(T, nx, ny, T_left, T_right, T_bottom, T_top)

    # Also record the BC type for informational purposes.
    bc_type = cfd_python.BC_TYPE_DIRICHLET
    print(f"  BC type applied:   {bc_type} (BC_TYPE_DIRICHLET)")

    # Convert to numpy for efficient Jacobi updates
    T_np = np.array(T, dtype=np.float64).reshape((ny, nx))

    # Fix the boundary rows/columns so they are never overwritten
    T_np[0, :] = T_bottom  # bottom row  (j = 0)
    T_np[-1, :] = T_top  # top row     (j = ny-1)
    T_np[:, 0] = T_left  # left column (i = 0)
    T_np[:, -1] = T_right  # right column (i = nx-1)

    iterations = 0
    for iteration in range(1, max_iterations + 1):
        T_old = T_np.copy()

        # Jacobi update for all interior nodes
        T_np[1:-1, 1:-1] = (
            0.25
            * (
                T_old[:-2, 1:-1]  # T[j-1, i]
                + T_old[2:, 1:-1]  # T[j+1, i]
                + T_old[1:-1, :-2]  # T[j, i-1]
                + T_old[1:-1, 2:]  # T[j, i+1]
            )
        )

        # Re-enforce boundary conditions (boundaries must not drift)
        T_np[0, :] = T_bottom
        T_np[-1, :] = T_top
        T_np[:, 0] = T_left
        T_np[:, -1] = T_right

        max_change = float(np.max(np.abs(T_np - T_old)))
        if max_change < tolerance:
            iterations = iteration
            print(f"  Converged after {iterations} iterations (max change = {max_change:.2e})")
            break
    else:
        iterations = max_iterations
        print(f"  Reached max iterations ({max_iterations}); last change = {max_change:.2e}")  # noqa: F821

    # Flatten back to a plain list for library API calls
    T_flat = T_np.flatten().tolist()

    # ------------------------------------------------------------------
    # Post-Processing
    # ------------------------------------------------------------------
    print("\nPost-Processing:")

    stats = cfd_python.calculate_field_stats(T_flat)
    print(f"  Min temperature:   {stats['min']:.4f} degC")
    print(f"  Max temperature:   {stats['max']:.4f} degC")
    print(f"  Avg temperature:   {stats['avg']:.4f} degC")

    # Centre-point temperature
    i_center = nx // 2
    j_center = ny // 2
    T_center = T_np[j_center, i_center]
    print(f"  Centre point ({i_center},{j_center}): T = {T_center:.4f} degC")

    # Write VTK output
    vtk_path = os.path.join(output_dir, "heat_conduction.vtk")
    cfd_python.write_vtk_scalar(
        vtk_path,
        "temperature",
        T_flat,
        nx,
        ny,
        xmin,
        xmax,
        ymin,
        ymax,
    )
    print("\nVTK output written: output/heat_conduction.vtk")

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    print("\nValidation:")

    # 1. Physical bounds: interior temperature must lie within [min_bc, max_bc]
    bc_min = min(T_left, T_right, T_top, T_bottom)
    bc_max = max(T_left, T_right, T_top, T_bottom)
    interior = T_np[1:-1, 1:-1]
    interior_min = float(np.min(interior))
    interior_max = float(np.max(interior))
    bounds_ok = (interior_min >= bc_min - tolerance) and (interior_max <= bc_max + tolerance)
    print(f"  Physical bounds [{bc_min:.1f}, {bc_max:.1f}] satisfied: {bounds_ok}")
    print(f"    Interior range: [{interior_min:.4f}, {interior_max:.4f}]")

    # 2. Heat flows left→right: left column average must exceed right column average
    T_left_avg = float(np.mean(T_np[:, 1]))
    T_right_avg = float(np.mean(T_np[:, -2]))
    gradient_ok = T_left_avg > T_right_avg
    print(f"  Left-to-right temperature gradient present: {gradient_ok}")
    print(f"    Near-left avg: {T_left_avg:.4f} degC, near-right avg: {T_right_avg:.4f} degC")

    # 3. Centre temperature is in the physically reasonable range
    T_bc_avg = (T_left + T_right + T_top + T_bottom) / 4.0
    center_reasonable = bc_min <= T_center <= bc_max
    print(
        f"  Centre temperature ({T_center:.4f}) in"
        f" [{bc_min:.1f}, {bc_max:.1f}]: {center_reasonable}"
    )
    print(f"  Boundary average for reference: {T_bc_avg:.2f} degC")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Grid size:              {nx} x {ny} = {nx * ny} nodes")
    print(f"  Boundary temperatures:  L={T_left} R={T_right}" f" T={T_top} B={T_bottom} (degC)")
    print(f"  Iterations to converge: {iterations}")
    print(f"  Min temperature:        {stats['min']:.4f} degC")
    print(f"  Max temperature:        {stats['max']:.4f} degC")
    print(f"  Avg temperature:        {stats['avg']:.4f} degC")
    print(f"  Centre temperature:     {T_center:.4f} degC")
    print("=" * 60)
    print("Heat conduction example complete!")


if __name__ == "__main__":
    main()
