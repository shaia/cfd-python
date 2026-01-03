#!/usr/bin/env python3
"""
Derived Fields and Statistics Example

This example demonstrates how to compute derived quantities and statistics
from flow fields using cfd_python.
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
    print("CFD Python Derived Fields Example")
    print("=" * 60)

    # =================================================================
    # 1. Run a Simulation to Get Flow Fields
    # =================================================================
    print("\n1. Running Simulation")
    print("-" * 60)

    nx, ny = 32, 32
    result = cfd_python.run_simulation_with_params(
        nx=nx, ny=ny, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0, steps=50, dt=0.001, cfl=0.2
    )

    print(f"   Grid: {nx} x {ny}")
    print(f"   Steps: {result['steps']}")
    print(f"   Solver: {result['solver_name']}")

    # =================================================================
    # 2. Compute Velocity Magnitude
    # =================================================================
    print("\n2. Computing Velocity Magnitude")
    print("-" * 60)

    # Create synthetic velocity fields for demonstrating compute_velocity_magnitude().
    # Note: run_simulation_with_params() returns only velocity_magnitude, not the
    # component fields. We create these synthetic fields to show the API usage.
    u = [0.0] * (nx * ny)
    v = [0.0] * (nx * ny)

    # Create a vortex-like velocity field
    cx, cy = nx // 2, ny // 2  # Center
    for j in range(ny):
        for i in range(nx):
            idx = j * nx + i
            dx = i - cx
            dy = j - cy
            r = (dx * dx + dy * dy) ** 0.5 + 0.1
            # Tangential velocity (vortex)
            u[idx] = -dy / r * 0.5
            v[idx] = dx / r * 0.5

    # Compute velocity magnitude using cfd_python
    vel_mag = cfd_python.compute_velocity_magnitude(u, v, nx, ny)

    print(f"   Velocity magnitude computed for {len(vel_mag)} points")
    print(f"   Min: {min(vel_mag):.6f}")
    print(f"   Max: {max(vel_mag):.6f}")

    # Compare with numpy (if available)
    u_np = np.array(u)
    v_np = np.array(v)
    vel_mag_np = np.sqrt(u_np**2 + v_np**2)
    print(f"   Numpy verification - Max diff: {np.max(np.abs(np.array(vel_mag) - vel_mag_np)):.2e}")

    # =================================================================
    # 3. Calculate Field Statistics
    # =================================================================
    print("\n3. Calculating Field Statistics")
    print("-" * 60)

    # Statistics for velocity magnitude
    stats = cfd_python.calculate_field_stats(vel_mag)
    print("   Velocity magnitude statistics:")
    print(f"     Min: {stats['min']:.6f}")
    print(f"     Max: {stats['max']:.6f}")
    print(f"     Avg: {stats['avg']:.6f}")
    print(f"     Sum: {stats['sum']:.6f}")

    # Statistics for u-velocity
    u_stats = cfd_python.calculate_field_stats(u)
    print("\n   U-velocity statistics:")
    print(f"     Min: {u_stats['min']:.6f}")
    print(f"     Max: {u_stats['max']:.6f}")
    print(f"     Avg: {u_stats['avg']:.6f}")

    # Statistics for v-velocity
    v_stats = cfd_python.calculate_field_stats(v)
    print("\n   V-velocity statistics:")
    print(f"     Min: {v_stats['min']:.6f}")
    print(f"     Max: {v_stats['max']:.6f}")
    print(f"     Avg: {v_stats['avg']:.6f}")

    # =================================================================
    # 4. Compute Comprehensive Flow Statistics
    # =================================================================
    print("\n4. Comprehensive Flow Statistics")
    print("-" * 60)

    # Create a pressure field
    p = [0.0] * (nx * ny)
    for j in range(ny):
        for i in range(nx):
            idx = j * nx + i
            dx = i - cx
            dy = j - cy
            r2 = dx * dx + dy * dy + 0.1
            # Pressure decreases toward center (vortex core)
            p[idx] = 1.0 - 0.5 / r2

    # Get all flow statistics at once
    flow_stats = cfd_python.compute_flow_statistics(u, v, p, nx, ny)

    print("   Full flow statistics:")
    for field_name in ["u", "v", "p", "velocity_magnitude"]:
        if field_name in flow_stats:
            field_stats = flow_stats[field_name]
            print(f"\n   {field_name}:")
            print(f"     Min: {field_stats['min']:.6f}")
            print(f"     Max: {field_stats['max']:.6f}")
            print(f"     Avg: {field_stats['avg']:.6f}")

    # =================================================================
    # 5. Practical Application: Convergence Monitoring
    # =================================================================
    print("\n5. Convergence Monitoring Example")
    print("-" * 60)

    print("   Simulating convergence monitoring...")

    # Track statistics over multiple steps
    max_velocities = []
    for step in range(5):
        # Run a few steps
        result = cfd_python.run_simulation_with_params(
            nx=nx, ny=ny, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0, steps=10, dt=0.001
        )
        vel_stats = cfd_python.calculate_field_stats(result["velocity_magnitude"])
        max_velocities.append(vel_stats["max"])
        print(f"     Step {(step+1)*10}: max_vel = {vel_stats['max']:.6f}")

    # Check for convergence (simplified)
    if len(max_velocities) >= 2:
        change = abs(max_velocities[-1] - max_velocities[-2])
        print(f"\n   Velocity change: {change:.2e}")

    # =================================================================
    # 6. VTK Output with Derived Fields
    # =================================================================
    print("\n6. VTK Output with Derived Fields")
    print("-" * 60)

    grid = cfd_python.create_grid(nx, ny, 0.0, 1.0, 0.0, 1.0)

    # Write velocity magnitude
    cfd_python.write_vtk_scalar(
        "velocity_magnitude.vtk",
        "velocity_magnitude",
        vel_mag,
        nx,
        ny,
        grid["xmin"],
        grid["xmax"],
        grid["ymin"],
        grid["ymax"],
    )
    print("   Written: velocity_magnitude.vtk")

    # Write pressure
    cfd_python.write_vtk_scalar(
        "pressure.vtk",
        "pressure",
        p,
        nx,
        ny,
        grid["xmin"],
        grid["xmax"],
        grid["ymin"],
        grid["ymax"],
    )
    print("   Written: pressure.vtk")

    # Write velocity vectors
    cfd_python.write_vtk_vector(
        "velocity_field.vtk",
        "velocity",
        u,
        v,
        nx,
        ny,
        grid["xmin"],
        grid["xmax"],
        grid["ymin"],
        grid["ymax"],
    )
    print("   Written: velocity_field.vtk")

    # =================================================================
    # Summary
    # =================================================================
    print("\n" + "=" * 60)
    print("Available Derived Field Functions:")
    print("  - compute_velocity_magnitude(u, v, nx, ny): sqrt(u^2 + v^2)")
    print("  - calculate_field_stats(data): min, max, avg, sum")
    print("  - compute_flow_statistics(u, v, p, nx, ny): all components")
    print("\nThese functions are useful for:")
    print("  - Post-processing simulation results")
    print("  - Monitoring convergence")
    print("  - Computing derived quantities for visualization")


if __name__ == "__main__":
    main()
