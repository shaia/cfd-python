#!/usr/bin/env python3
"""
Lid-Driven Cavity Flow - Advanced Example

This example demonstrates a complete lid-driven cavity simulation with:
- Proper boundary condition setup
- Time stepping with convergence monitoring
- Post-processing and visualization output
- Statistics tracking

Physics Background:
-------------------
The lid-driven cavity is a fundamental CFD benchmark problem. A square (or
rectangular) cavity has:
- Three stationary walls (no-slip: u = v = 0)
- One moving wall (lid) with prescribed velocity (u = U_lid, v = 0)

The moving lid drags fluid along, creating:
1. A primary vortex in the center rotating with the lid
2. Secondary corner vortices at low Reynolds numbers
3. Complex vortex structures at high Reynolds numbers

Reynolds Number (Re):
Re = U_lid * L / ν  where L is cavity size, ν is kinematic viscosity

- Re < 100: Single primary vortex, steady flow
- Re ~ 1000: Secondary vortices appear in corners
- Re > 3000: Flow becomes unsteady, then turbulent

Numerical Considerations:
- Time step limited by CFL condition (advection) and diffusion stability
- Grid resolution affects vortex capture and accuracy
- Convergence monitored by velocity change between steps

This is the standard validation case for incompressible Navier-Stokes solvers.
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

    Note: This example demonstrates the API usage pattern for monitoring convergence
    and writing output. The current `run_simulation_with_params()` API runs a fresh
    simulation each call and returns velocity magnitude - it doesn't expose the
    internal u, v, p fields for true time-stepping continuation. Each iteration
    here runs an independent simulation with increasing step counts to show how
    the solution evolves.

    Args:
        nx, ny: Grid dimensions
        Re: Reynolds number
        steps: Total time steps (used for progress monitoring)
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
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    cfd_python.set_output_dir(output_dir)

    # Initialize fields
    u, v, p = setup_lid_driven_cavity(nx, ny, lid_velocity)

    # Track convergence across different step counts
    max_velocities = []  # Max velocity at each sample point
    residuals = []  # Relative change between samples

    # Run simulation and track convergence by comparing results at different step counts
    # Note: The API runs a fresh simulation each call, so we sample at key intervals
    # to show how the solution evolves with more time steps.
    print("\nRunning convergence study...")
    print(f"{'Steps':>6} {'Max Vel':>12} {'Avg Vel':>12} {'Change':>12}")
    print("-" * 48)

    prev_max = 0.0
    sample_steps = [1, 5, 10, 25, 50, 100, 150, 200]
    sample_steps = [s for s in sample_steps if s <= steps]
    if steps not in sample_steps:
        sample_steps.append(steps)

    for sim_steps in sample_steps:
        try:
            result = cfd_python.run_simulation_with_params(
                nx=nx,
                ny=ny,
                xmin=xmin,
                xmax=xmax,
                ymin=ymin,
                ymax=ymax,
                steps=sim_steps,
                dt=dt,
                cfl=0.25,
            )

            # Check status
            status = cfd_python.get_last_status()
            if status != cfd_python.CFD_SUCCESS:
                cfd_python.raise_for_status(status, context=f"steps={sim_steps}")

        except cfd_python.CFDError as e:
            print(f"Simulation error at steps={sim_steps}: {e}")
            break

        # Get velocity magnitude from result
        vel_mag = result["velocity_magnitude"]

        # Compute statistics
        stats = cfd_python.calculate_field_stats(vel_mag)
        max_vel = stats["max"]
        max_velocities.append(max_vel)

        # Compute change from previous sample
        if prev_max > 0:
            change = abs(max_vel - prev_max) / prev_max
            residuals.append(change)
        else:
            change = float("inf")

        prev_max = max_vel

        print(f"{sim_steps:6d} {stats['max']:12.6f} {stats['avg']:12.6f} {change:12.2e}")

        # Write VTK output at final step
        if sim_steps == steps:
            filename = os.path.join(output_dir, "cavity_final.vtk")
            cfd_python.write_vtk_scalar(
                filename, "velocity_magnitude", vel_mag, nx, ny, xmin, xmax, ymin, ymax
            )

    print("\nSimulation complete!")
    print("Output files written to: output/")

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

    print("\nOutput directory: output/")


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

    # Run parameter study: grid resolution effect
    # Note: The current API doesn't expose viscosity/Reynolds number parameters,
    # so we demonstrate grid resolution effects instead.
    print("\n" + "=" * 60)
    print("Parameter Study: Effect of Grid Resolution")
    print("=" * 60)

    for grid_size in [16, 32, 48]:
        result = cfd_python.run_simulation_with_params(
            nx=grid_size, ny=grid_size, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0, steps=100, dt=0.0001
        )
        stats = cfd_python.calculate_field_stats(result["velocity_magnitude"])
        print(f"  {grid_size}x{grid_size}: max_vel={stats['max']:.4f}, avg_vel={stats['avg']:.4f}")


if __name__ == "__main__":
    main()
