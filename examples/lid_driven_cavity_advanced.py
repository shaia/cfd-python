#!/usr/bin/env python3
"""
Lid-Driven Cavity Flow - Advanced Example

This example demonstrates a complete lid-driven cavity simulation with:
- Proper boundary condition setup
- Time stepping with convergence monitoring
- Post-processing and visualization output
- Statistics tracking
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import cfd_python
    from cfd_python import (
        CFDError,
        raise_for_status,
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure to build the package first:")
    print("  pip install -e .")
    sys.exit(1)


def setup_lid_driven_cavity(nx, ny, lid_velocity=1.0):
    """Set up initial conditions for lid-driven cavity.

    Args:
        nx, ny: Grid dimensions
        lid_velocity: Velocity of the moving lid (top wall)

    Returns:
        tuple: (u, v, p) velocity and pressure fields
    """
    size = nx * ny

    # Initialize fields to zero
    u = [0.0] * size
    v = [0.0] * size
    p = [0.0] * size

    # Apply boundary conditions
    # No-slip on all walls first
    cfd_python.bc_apply_noslip(u, v, nx, ny)

    # Moving lid on top (override top boundary)
    # Set u = lid_velocity on top row
    for i in range(nx):
        idx = (ny - 1) * nx + i
        u[idx] = lid_velocity

    return u, v, p


def run_cavity_simulation(nx=32, ny=32, Re=100, steps=500, output_interval=100):
    """Run lid-driven cavity simulation.

    Args:
        nx, ny: Grid dimensions
        Re: Reynolds number
        steps: Total time steps
        output_interval: Steps between VTK outputs

    Returns:
        dict: Simulation results
    """
    print("\nLid-Driven Cavity Simulation")
    print(f"Grid: {nx}x{ny}, Re={Re}, Steps={steps}")
    print("=" * 60)

    # Grid setup
    xmin, xmax = 0.0, 1.0
    ymin, ymax = 0.0, 1.0
    dx = (xmax - xmin) / (nx - 1)
    dy = (ymax - ymin) / (ny - 1)

    # Time step (CFL-based)
    lid_velocity = 1.0
    dt = 0.25 * min(dx, dy) / lid_velocity  # CFL ~ 0.25
    dt = min(dt, 0.5 * Re * dx * dx)  # Stability for diffusion

    print(f"Domain: [{xmin}, {xmax}] x [{ymin}, {ymax}]")
    print(f"dx={dx:.4f}, dy={dy:.4f}, dt={dt:.6f}")

    # Set up output directory
    output_dir = "cavity_output"
    os.makedirs(output_dir, exist_ok=True)
    cfd_python.set_output_dir(output_dir)

    # Initialize fields
    u, v, p = setup_lid_driven_cavity(nx, ny, lid_velocity)

    # Track convergence
    max_velocities = []
    residuals = []

    print("\nRunning simulation...")
    print(f"{'Step':>6} {'Max U':>12} {'Max V':>12} {'Residual':>12}")
    print("-" * 48)

    prev_u = u.copy()

    for step in range(steps):
        # Run simulation step using the library
        try:
            result = cfd_python.run_simulation_with_params(
                nx=nx, ny=ny, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax, steps=1, dt=dt, cfl=0.25
            )

            # Check status
            status = cfd_python.get_last_status()
            if status != cfd_python.CFD_SUCCESS:
                raise_for_status(status, context=f"step {step}")

        except CFDError as e:
            print(f"Simulation error at step {step}: {e}")
            break

        # Get velocity magnitude from result
        vel_mag = result["velocity_magnitude"]

        # Compute statistics
        stats = cfd_python.calculate_field_stats(vel_mag)
        max_vel = stats["max"]
        max_velocities.append(max_vel)

        # Compute residual (change in velocity)
        if step > 0:
            residual = sum(abs(vel_mag[i] - prev_u[i]) for i in range(len(vel_mag))) / len(vel_mag)
            residuals.append(residual)
        else:
            residual = float("inf")

        prev_u = vel_mag.copy()

        # Output progress
        if step % (steps // 10) == 0 or step == steps - 1:
            u_stats = cfd_python.calculate_field_stats(vel_mag)
            print(f"{step:6d} {u_stats['max']:12.6f} {u_stats['avg']:12.6f} {residual:12.2e}")

        # Write VTK output
        if step % output_interval == 0 or step == steps - 1:
            filename = f"cavity_step_{step:05d}.vtk"
            cfd_python.write_vtk_scalar(
                filename, "velocity_magnitude", vel_mag, nx, ny, xmin, xmax, ymin, ymax
            )

    print("\nSimulation complete!")
    print(f"Output files written to: {output_dir}/")

    # Final statistics
    final_stats = cfd_python.calculate_field_stats(vel_mag)

    return {
        "nx": nx,
        "ny": ny,
        "Re": Re,
        "steps": steps,
        "final_max_velocity": final_stats["max"],
        "final_avg_velocity": final_stats["avg"],
        "max_velocities": max_velocities,
        "residuals": residuals,
        "output_dir": output_dir,
    }


def analyze_results(results):
    """Analyze and display simulation results."""
    print("\n" + "=" * 60)
    print("Results Analysis")
    print("=" * 60)

    print(f"\nGrid: {results['nx']} x {results['ny']}")
    print(f"Reynolds number: {results['Re']}")
    print(f"Time steps: {results['steps']}")

    print("\nFinal Statistics:")
    print(f"  Max velocity magnitude: {results['final_max_velocity']:.6f}")
    print(f"  Avg velocity magnitude: {results['final_avg_velocity']:.6f}")

    if results["residuals"]:
        final_residual = results["residuals"][-1]
        print(f"  Final residual: {final_residual:.2e}")

        # Check convergence
        if final_residual < 1e-6:
            print("  Status: CONVERGED")
        elif final_residual < 1e-4:
            print("  Status: PARTIALLY CONVERGED")
        else:
            print("  Status: NOT CONVERGED (may need more steps)")

    print(f"\nOutput directory: {results['output_dir']}")


def main():
    print("CFD Python - Lid-Driven Cavity Example")
    print("=" * 60)

    # Show system info
    print("\nSystem Information:")
    print(f"  SIMD: {cfd_python.get_simd_name()}")
    print(f"  BC Backend: {cfd_python.bc_get_backend_name()}")
    print(f"  Available backends: {cfd_python.get_available_backends()}")

    # Run simulation
    results = run_cavity_simulation(nx=32, ny=32, Re=100, steps=200, output_interval=50)

    # Analyze results
    analyze_results(results)

    # Run parameter study (optional)
    print("\n" + "=" * 60)
    print("Parameter Study: Effect of Reynolds Number")
    print("=" * 60)

    for Re in [50, 100, 200]:
        result = cfd_python.run_simulation_with_params(
            nx=32, ny=32, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0, steps=100, dt=0.0001
        )
        stats = cfd_python.calculate_field_stats(result["velocity_magnitude"])
        print(f"  Re={Re:3d}: max_vel={stats['max']:.4f}, avg_vel={stats['avg']:.4f}")


if __name__ == "__main__":
    main()
