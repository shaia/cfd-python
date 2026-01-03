#!/usr/bin/env python3
"""
Channel Flow Example

This example demonstrates setting up a channel flow simulation with:
- Parabolic inlet velocity profile
- Zero-gradient outlet
- No-slip walls on top and bottom
- Periodic or developed flow analysis
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


def setup_channel_flow(nx, ny, u_max=1.0):
    """Set up initial conditions for channel flow.

    Args:
        nx, ny: Grid dimensions
        u_max: Maximum inlet velocity

    Returns:
        tuple: (u, v, p) velocity and pressure fields
    """
    size = nx * ny

    # Initialize fields
    u = [0.0] * size
    v = [0.0] * size
    p = [0.0] * size

    # Apply inlet BC (parabolic profile on left edge)
    cfd_python.bc_apply_inlet_parabolic(u, v, nx, ny, u_max, cfd_python.BC_EDGE_LEFT)

    # Apply outlet BC (zero-gradient on right edge)
    cfd_python.bc_apply_outlet_velocity(u, v, nx, ny, cfd_python.BC_EDGE_RIGHT)

    # Apply no-slip walls on top and bottom
    # Note: bc_apply_noslip applies to all boundaries, so we apply walls specifically
    for i in range(nx):
        # Bottom wall (j=0)
        idx_bottom = i
        u[idx_bottom] = 0.0
        v[idx_bottom] = 0.0

        # Top wall (j=ny-1)
        idx_top = (ny - 1) * nx + i
        u[idx_top] = 0.0
        v[idx_top] = 0.0

    return u, v, p


def compute_analytical_solution(nx, ny, u_max, H):
    """Compute analytical Poiseuille flow solution for validation.

    This is a reference implementation for comparing simulation results
    against the known analytical solution for fully developed channel flow.

    For Poiseuille flow, the velocity profile is parabolic:
    u(y) = u_max * 4 * (y/H) * (1 - y/H)

    The factor of 4 ensures that u_max occurs at the centerline (y = H/2),
    where the formula evaluates to u_max * 4 * 0.5 * 0.5 = u_max.
    At the walls (y = 0 and y = H), velocity is zero (no-slip condition).

    Args:
        nx, ny: Grid dimensions
        u_max: Maximum velocity at the channel centerline (y = H/2)
        H: Channel height

    Returns:
        list: Analytical velocity field for comparison with simulation
    """
    u_analytical = [0.0] * (nx * ny)
    dy = H / (ny - 1)

    for j in range(ny):
        y = j * dy
        # Parabolic profile
        u_y = u_max * 4.0 * (y / H) * (1.0 - y / H)

        for i in range(nx):
            idx = j * nx + i
            u_analytical[idx] = u_y

    return u_analytical


def main():
    print("CFD Python - Channel Flow Example")
    print("=" * 60)

    # Parameters
    nx, ny = 64, 32  # Longer in x for channel flow
    xmin, xmax = 0.0, 4.0  # Channel length = 4
    ymin, ymax = 0.0, 1.0  # Channel height = 1
    u_max = 1.0  # Maximum inlet velocity

    print("\nChannel Configuration:")
    print(f"  Grid: {nx} x {ny}")
    print(f"  Length: {xmax - xmin}")
    print(f"  Height: {ymax - ymin}")
    print(f"  Max inlet velocity: {u_max}")

    # Show backend info
    print("\nBackend Information:")
    print(f"  SIMD: {cfd_python.get_simd_name()}")
    print(f"  BC Backend: {cfd_python.bc_get_backend_name()}")

    # Set up flow - demonstrates how to configure boundary conditions
    # Note: setup_channel_flow shows BC API usage; run_simulation_with_params
    # creates its own internal fields. The u, v here are used to verify
    # the BC setup (inlet profile, cross-section profiles).
    print("\nSetting up channel flow (BC demonstration)...")
    u, v, _ = setup_channel_flow(nx, ny, u_max)

    # Verify inlet profile (parabolic velocity distribution)
    print("\nInlet velocity profile (left edge):")
    print(f"  {'j':>4}  {'y':>8}  {'u':>10}")
    print("  " + "-" * 26)
    for j in range(0, ny, max(1, ny // 8)):
        y = ymin + j * (ymax - ymin) / (ny - 1)
        idx = j * nx  # Left edge
        print(f"  {j:4d}  {y:8.4f}  {u[idx]:10.6f}")

    # Run simulation
    print("\nRunning simulation...")
    steps = 100

    result = cfd_python.run_simulation_with_params(
        nx=nx, ny=ny, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax, steps=steps, dt=0.001, cfl=0.2
    )

    print(f"  Completed {steps} steps")
    print(f"  Solver: {result['solver_name']}")

    # Compute statistics from simulation result
    vel_mag = result["velocity_magnitude"]
    vel_mag_stats = cfd_python.calculate_field_stats(vel_mag)

    print("\nSimulation Results:")
    print("  Velocity magnitude:")
    print(f"    Min: {vel_mag_stats['min']:.6f}")
    print(f"    Max: {vel_mag_stats['max']:.6f}")
    print(f"    Avg: {vel_mag_stats['avg']:.6f}")

    # Check centerline velocity
    centerline_velocities = []
    j_center = ny // 2
    for i in range(nx):
        idx = j_center * nx + i
        centerline_velocities.append(u[idx])

    print(f"\nCenterline velocity (j={j_center}):")
    print(f"  Inlet:  {centerline_velocities[0]:.6f}")
    print(f"  Center: {centerline_velocities[nx//2]:.6f}")
    print(f"  Outlet: {centerline_velocities[-1]:.6f}")

    # Compare with analytical solution
    print("\nAnalytical Comparison:")
    u_analytical = compute_analytical_solution(nx, ny, u_max, ymax - ymin)
    u_analytical_stats = cfd_python.calculate_field_stats(u_analytical)
    print(f"  Analytical max velocity: {u_analytical_stats['max']:.6f}")
    print(f"  Simulated max velocity:  {vel_mag_stats['max']:.6f}")

    # Write output
    print("\nWriting VTK output...")

    # Velocity magnitude
    cfd_python.write_vtk_scalar(
        "channel_velocity_magnitude.vtk",
        "velocity_magnitude",
        vel_mag,
        nx,
        ny,
        xmin,
        xmax,
        ymin,
        ymax,
    )

    # Velocity vectors
    cfd_python.write_vtk_vector(
        "channel_velocity.vtk", "velocity", u, v, nx, ny, xmin, xmax, ymin, ymax
    )

    print("  channel_velocity_magnitude.vtk")
    print("  channel_velocity.vtk")

    # Cross-section profiles
    print("\n" + "=" * 60)
    print("Cross-section velocity profiles (u vs y):")
    print("=" * 60)

    x_positions = [0, nx // 4, nx // 2, 3 * nx // 4, nx - 1]
    x_labels = ["Inlet", "x=L/4", "x=L/2", "x=3L/4", "Outlet"]

    print(f"\n{'y':>8}", end="")
    for label in x_labels:
        print(f"  {label:>10}", end="")
    print()
    print("-" * (8 + 12 * len(x_labels)))

    for j in range(0, ny, max(1, ny // 10)):
        y = ymin + j * (ymax - ymin) / (ny - 1)
        print(f"{y:8.4f}", end="")
        for i in x_positions:
            idx = j * nx + i
            print(f"  {u[idx]:10.6f}", end="")
        print()

    print("\n" + "=" * 60)
    print("Channel flow example complete!")


if __name__ == "__main__":
    main()
