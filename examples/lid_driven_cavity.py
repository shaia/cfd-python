#!/usr/bin/env python3
"""
Lid-Driven Cavity Example

The lid-driven cavity is a classic CFD benchmark problem.
A square cavity has a moving lid at the top, driving fluid motion.

This example demonstrates:
- Setting up a standard CFD benchmark
- Running with different grid resolutions
- Comparing solver performance
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import cfd_python
import numpy as np
import tempfile
from pathlib import Path


def run_cavity_simulation(nx, ny, steps, solver_type=None, output_dir=None):
    """Run a lid-driven cavity simulation."""
    kwargs = {
        'nx': nx,
        'ny': ny,
        'steps': steps,
        'xmin': 0.0,
        'xmax': 1.0,
        'ymin': 0.0,
        'ymax': 1.0,
    }

    if solver_type:
        kwargs['solver_type'] = solver_type

    if output_dir:
        kwargs['output_file'] = str(output_dir / f"cavity_{nx}x{ny}_{steps}steps.vtk")

    result = cfd_python.run_simulation(**kwargs)
    return np.array(result).reshape((ny, nx))


def analyze_results(vel_mag, nx, ny):
    """Analyze the velocity field."""
    # Find vortex center (location of minimum velocity in central region)
    center_region = vel_mag[ny//4:3*ny//4, nx//4:3*nx//4]
    min_idx = np.unravel_index(np.argmin(center_region), center_region.shape)

    # Adjust indices for full grid
    vortex_y = min_idx[0] + ny//4
    vortex_x = min_idx[1] + nx//4

    # Normalize to [0,1] domain
    vortex_x_norm = vortex_x / (nx - 1)
    vortex_y_norm = vortex_y / (ny - 1)

    return {
        'max_velocity': np.max(vel_mag),
        'min_velocity': np.min(vel_mag),
        'mean_velocity': np.mean(vel_mag),
        'vortex_center': (vortex_x_norm, vortex_y_norm),
    }


def main():
    print("CFD Python - Lid-Driven Cavity Example")
    print("=" * 50)
    print("\nThe lid-driven cavity is a classic CFD benchmark.")
    print("A square cavity has a moving lid at the top.")

    # Create output directory
    output_dir = Path(tempfile.mkdtemp(prefix="cavity_"))
    print(f"\nOutput directory: {output_dir}")

    # Grid convergence study
    print("\n1. Grid Convergence Study")
    print("-" * 50)

    grid_sizes = [16, 32, 64]
    steps = 100
    results = []

    for n in grid_sizes:
        print(f"\n   Running {n}x{n} grid with {steps} steps...")
        vel_mag = run_cavity_simulation(n, n, steps, output_dir=output_dir)
        analysis = analyze_results(vel_mag, n, n)

        results.append({
            'grid': n,
            **analysis
        })

        print(f"   Max velocity: {analysis['max_velocity']:.6f}")
        print(f"   Vortex center: ({analysis['vortex_center'][0]:.3f}, {analysis['vortex_center'][1]:.3f})")

    # Reference values (Ghia et al., 1982 for Re=100)
    print("\n2. Comparison with Reference Data")
    print("-" * 50)
    print("   Reference: Ghia et al. (1982), Re=100")
    print("   Expected vortex center: approximately (0.62, 0.74)")
    print()

    for r in results:
        vx, vy = r['vortex_center']
        print(f"   Grid {r['grid']:3d}x{r['grid']:<3d}: vortex at ({vx:.3f}, {vy:.3f})")

    # Solver comparison
    print("\n3. Solver Comparison")
    print("-" * 50)

    solvers = cfd_python.list_solvers()
    nx, ny = 32, 32
    steps = 50

    print(f"\n   Testing on {nx}x{ny} grid with {steps} steps:\n")

    for solver in solvers:
        try:
            vel_mag = run_cavity_simulation(nx, ny, steps, solver_type=solver)
            analysis = analyze_results(vel_mag, nx, ny)
            print(f"   {solver:30s}: max_vel={analysis['max_velocity']:.6f}")
        except Exception as e:
            print(f"   {solver:30s}: Failed - {e}")

    # Summary
    print("\n" + "=" * 50)
    print("Lid-Driven Cavity Summary")
    print("=" * 50)

    print("\nGrid Convergence Results:")
    for r in results:
        print(f"  {r['grid']}x{r['grid']}: max_vel={r['max_velocity']:.6f}")

    print(f"\nOutput files saved to: {output_dir}")
    for f in sorted(output_dir.iterdir()):
        print(f"  - {f.name}")

    print("\nTo visualize in ParaView:")
    print("  1. Open the .vtk files")
    print("  2. Apply 'Contour' or 'Surface' representation")
    print("  3. Color by velocity magnitude")


if __name__ == "__main__":
    main()
