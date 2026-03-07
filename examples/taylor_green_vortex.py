#!/usr/bin/env python3
"""
Taylor-Green Vortex Decay Example

This example demonstrates validation of a CFD solver against an exact unsteady
analytical solution to the 2D incompressible Navier-Stokes equations.

Physics Background:
-------------------
The 2D Taylor-Green vortex is one of the few cases where the incompressible
Navier-Stokes equations admit a closed-form, time-dependent exact solution.
It describes the viscous decay of a periodic vortex array and is the canonical
benchmark for verifying temporal accuracy and measuring numerical dissipation.

Exact solution on the domain [0, 2*pi] x [0, 2*pi]:

    u(x, y, t) =  cos(x) sin(y) exp(-2nut)
    v(x, y, t) = -sin(x) cos(y) exp(-2nut)
    p(x, y, t) = -(cos(2x) + cos(2y)) / 4 * exp(-4nut)

where nu is the kinematic viscosity.  The velocity field decays exponentially
with time constant tau = 1/(2nu).  Pressure decays twice as fast (tau_p = 1/(4nu))
because it is quadratic in velocity.

Key validation metrics:
  - L2 error norm: measures global accuracy of the numerical solution
  - Max pointwise error: worst-case deviation from the exact solution
  - Kinetic energy dissipation rate: should match -4nu * E(0) * exp(-4nut)
  - Dissipation error: difference between numerical and analytical energy decay

The boundary conditions are periodic in both x and y, consistent with the
cos/sin basis functions of the exact solution.
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


def taylor_green_velocity(nx, ny, xmin, xmax, ymin, ymax, nu, t):
    """Evaluate the exact Taylor-Green velocity field at time t.

    Args:
        nx, ny: Grid point counts in x and y
        xmin, xmax, ymin, ymax: Domain bounds
        nu: Kinematic viscosity
        t: Evaluation time

    Returns:
        tuple: (u, v) as flat Python lists, row-major (j * nx + i)
    """
    dx = (xmax - xmin) / nx
    dy = (ymax - ymin) / ny
    decay = np.exp(-2.0 * nu * t)

    u = np.empty(nx * ny)
    v = np.empty(nx * ny)

    for j in range(ny):
        y = ymin + (j + 0.5) * dy  # cell-centred
        for i in range(nx):
            x = xmin + (i + 0.5) * dx
            idx = j * nx + i
            u[idx] = np.cos(x) * np.sin(y) * decay
            v[idx] = -np.sin(x) * np.cos(y) * decay

    return u.tolist(), v.tolist()


def taylor_green_pressure(nx, ny, xmin, xmax, ymin, ymax, nu, t):
    """Evaluate the exact Taylor-Green pressure field at time t.

    Args:
        nx, ny: Grid point counts in x and y
        xmin, xmax, ymin, ymax: Domain bounds
        nu: Kinematic viscosity
        t: Evaluation time

    Returns:
        list: Pressure field as a flat Python list
    """
    dx = (xmax - xmin) / nx
    dy = (ymax - ymin) / ny
    decay = np.exp(-4.0 * nu * t)

    p = np.empty(nx * ny)

    for j in range(ny):
        y = ymin + (j + 0.5) * dy
        for i in range(nx):
            x = xmin + (i + 0.5) * dx
            idx = j * nx + i
            p[idx] = -(np.cos(2.0 * x) + np.cos(2.0 * y)) / 4.0 * decay

    return p.tolist()


def kinetic_energy(vel_mag_list):
    """Compute the domain-averaged kinetic energy from a velocity magnitude field.

    KE = (1 / N) * sum(0.5 * |V|^2)

    Args:
        vel_mag_list: Flat list of |V| values
        nx, ny: Grid dimensions (used only to confirm size)

    Returns:
        float: Domain-averaged kinetic energy
    """
    vm = np.array(vel_mag_list)
    return float(np.mean(0.5 * vm * vm))


def l2_error(numerical, analytical):
    """Compute the L2 error norm between two flat field lists.

    L2 = sqrt( mean( (numerical - analytical)^2 ) )

    Args:
        numerical: Flat list of numerical values
        analytical: Flat list of analytical values (same length)
        nx, ny: Grid dimensions

    Returns:
        float: L2 error norm
    """
    num = np.array(numerical)
    ana = np.array(analytical)
    return float(np.sqrt(np.mean((num - ana) ** 2)))


def main():
    print("CFD Python - Taylor-Green Vortex Decay")
    print("=" * 60)

    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    # =================================================================
    # Problem Setup
    # =================================================================
    print("\n1. Problem Setup")
    print("-" * 60)

    nx, ny = 32, 32
    xmin, xmax = 0.0, 2.0 * np.pi
    ymin, ymax = 0.0, 2.0 * np.pi

    # Kinematic viscosity: nu = 0.05 gives visible but incomplete decay over
    # the integration window; tau = 1/(2nu) = 10 time units.
    nu = 0.05

    # Time integration parameters
    steps = 100
    dt = 0.001
    cfl = 0.2
    t_final = steps * dt

    # Characteristic velocity scale: max |V| at t=0 is 1/sqrt(2) ~ 0.707
    u_ref = 1.0 / np.sqrt(2.0)
    L_ref = 2.0 * np.pi
    Re = u_ref * L_ref / nu

    # Analytical decay factor at final time
    decay_final = np.exp(-2.0 * nu * t_final)

    print(f"   Grid:            {nx} x {ny}")
    print("   Domain:          [0, 2*pi] x [0, 2*pi]")
    print(f"   Kinematic nu:     {nu}")
    print(f"   Reynolds number: {Re:.2f}  (U_ref * 2*pi / nu)")
    print(f"   Time step dt:    {dt}")
    print(f"   CFL limit:       {cfl}")
    print(f"   Steps:           {steps}")
    print(f"   Final time:      {t_final:.4f}")
    print(f"   Decay factor:    exp(-2nuT) = {decay_final:.6f}")
    print(f"   Expected % decay of |V|_max: {(1.0 - decay_final) * 100:.1f}%")

    # Discover available solvers
    solvers = cfd_python.list_solvers()
    print(f"\n   Available solvers: {', '.join(solvers)}")

    # =================================================================
    # Initial Condition
    # =================================================================
    print("\n2. Initial Condition (t = 0)")
    print("-" * 60)

    u0, v0 = taylor_green_velocity(nx, ny, xmin, xmax, ymin, ymax, nu, t=0.0)
    vm0 = cfd_python.compute_velocity_magnitude(u0, v0, nx, ny)
    stats0 = cfd_python.calculate_field_stats(vm0)
    ke0 = kinetic_energy(vm0)

    print("   Velocity magnitude |V| at t=0:")
    print(f"     Min: {stats0['min']:.6f}")
    print(f"     Max: {stats0['max']:.6f}  (exact: {1.0 / np.sqrt(2.0):.6f})")
    print(f"     Avg: {stats0['avg']:.6f}")
    print(f"   Kinetic energy KE(0): {ke0:.6f}")

    # Write initial velocity field to VTK
    cfd_python.write_vtk_vector(
        os.path.join(output_dir, "tgv_velocity_t0.vtk"),
        "velocity",
        u0,
        v0,
        nx,
        ny,
        xmin,
        xmax,
        ymin,
        ymax,
    )
    cfd_python.write_vtk_scalar(
        os.path.join(output_dir, "tgv_velocity_magnitude_t0.vtk"),
        "velocity_magnitude",
        vm0,
        nx,
        ny,
        xmin,
        xmax,
        ymin,
        ymax,
    )
    print("\n   Written: output/tgv_velocity_t0.vtk")
    print("   Written: output/tgv_velocity_magnitude_t0.vtk")

    # =================================================================
    # Simulation
    # =================================================================
    print("\n3. Running Simulation")
    print("-" * 60)

    print(f"   Integrating {steps} steps with dt={dt} ...")

    result = cfd_python.run_simulation_with_params(
        nx=nx,
        ny=ny,
        xmin=xmin,
        xmax=xmax,
        ymin=ymin,
        ymax=ymax,
        steps=steps,
        dt=dt,
        cfl=cfl,
    )

    print(f"   Completed {result['steps']} steps")
    print(f"   Solver: {result['solver_name']}")

    vm_num = result["velocity_magnitude"]
    stats_num = cfd_python.calculate_field_stats(vm_num)
    ke_num = kinetic_energy(vm_num)

    print(f"\n   Numerical |V| at t={t_final:.4f}:")
    print(f"     Min: {stats_num['min']:.6f}")
    print(f"     Max: {stats_num['max']:.6f}")
    print(f"     Avg: {stats_num['avg']:.6f}")
    print(f"   Numerical KE({t_final:.4f}): {ke_num:.6f}")

    # Write final numerical velocity magnitude to VTK
    cfd_python.write_vtk_scalar(
        os.path.join(output_dir, "tgv_velocity_magnitude_final_numerical.vtk"),
        "velocity_magnitude",
        vm_num,
        nx,
        ny,
        xmin,
        xmax,
        ymin,
        ymax,
    )
    print("\n   Written: output/tgv_velocity_magnitude_final_numerical.vtk")

    # =================================================================
    # Post-Processing: Analytical Solution at Final Time
    # =================================================================
    print("\n4. Post-Processing: Analytical Solution at t_final")
    print("-" * 60)

    u_ana, v_ana = taylor_green_velocity(nx, ny, xmin, xmax, ymin, ymax, nu, t=t_final)
    vm_ana = cfd_python.compute_velocity_magnitude(u_ana, v_ana, nx, ny)
    stats_ana = cfd_python.calculate_field_stats(vm_ana)
    ke_ana = kinetic_energy(vm_ana)

    print(f"   Analytical |V| at t={t_final:.4f}:")
    print(f"     Min: {stats_ana['min']:.6f}")
    print(f"     Max: {stats_ana['max']:.6f}  (exact: {u_ref * decay_final:.6f})")
    print(f"     Avg: {stats_ana['avg']:.6f}")
    print(f"   Analytical KE({t_final:.4f}): {ke_ana:.6f}")

    # Write analytical velocity fields to VTK
    cfd_python.write_vtk_vector(
        os.path.join(output_dir, "tgv_velocity_analytical_final.vtk"),
        "velocity",
        u_ana,
        v_ana,
        nx,
        ny,
        xmin,
        xmax,
        ymin,
        ymax,
    )
    cfd_python.write_vtk_scalar(
        os.path.join(output_dir, "tgv_velocity_magnitude_final_analytical.vtk"),
        "velocity_magnitude",
        vm_ana,
        nx,
        ny,
        xmin,
        xmax,
        ymin,
        ymax,
    )
    print("\n   Written: output/tgv_velocity_analytical_final.vtk")
    print("   Written: output/tgv_velocity_magnitude_final_analytical.vtk")

    # =================================================================
    # Validation: Error Norms and Energy Decay
    # =================================================================
    print("\n5. Validation")
    print("-" * 60)

    # L2 error of velocity magnitude field
    l2 = l2_error(vm_num, vm_ana)

    # Max pointwise error
    vm_num_np = np.array(vm_num)
    vm_ana_np = np.array(vm_ana)
    err_field = np.abs(vm_num_np - vm_ana_np)
    max_err = float(np.max(err_field))

    # Relative L2 error (normalised by analytical RMS)
    rms_ana = float(np.sqrt(np.mean(vm_ana_np**2)))
    rel_l2 = l2 / rms_ana if rms_ana > 0.0 else float("inf")

    # Energy dissipation: analytical KE decays as KE(0) * exp(-4nut)
    ke_ana_exact = ke0 * np.exp(-4.0 * nu * t_final)
    dissipation_error = abs(ke_num - ke_ana_exact)
    relative_diss_error = dissipation_error / ke_ana_exact if ke_ana_exact > 0.0 else float("inf")

    # Numerical dissipation estimate: excess energy loss beyond analytical decay
    numerical_dissipation = ke_ana_exact - ke_num  # positive = over-dissipated

    print(f"   L2 error (|V| field):          {l2:.4e}")
    print(f"   Relative L2 error:             {rel_l2:.4e}  ({rel_l2 * 100:.2f}%)")
    print(f"   Max pointwise error:           {max_err:.4e}")
    print(f"   KE numerical:                  {ke_num:.6f}")
    print(f"   KE analytical (exact):         {ke_ana_exact:.6f}")
    print(f"   KE dissipation error:          {dissipation_error:.4e}")
    print(f"   Relative KE error:             {relative_diss_error * 100:.2f}%")
    if numerical_dissipation >= 0.0:
        print(f"   Numerical dissipation:         {numerical_dissipation:.4e}  (over-dissipated)")
    else:
        diss = abs(numerical_dissipation)
        print(f"   Numerical dissipation:         {diss:.4e}  (under-dissipated)")

    # Write error field to VTK for spatial inspection
    err_list = err_field.tolist()
    cfd_python.write_vtk_scalar(
        os.path.join(output_dir, "tgv_error_field.vtk"),
        "velocity_magnitude_error",
        err_list,
        nx,
        ny,
        xmin,
        xmax,
        ymin,
        ymax,
    )
    print("\n   Written: output/tgv_error_field.vtk")

    # =================================================================
    # Summary
    # =================================================================
    print("\n" + "=" * 60)
    print("Taylor-Green Vortex Decay - Summary")
    print("=" * 60)
    print(f"  Grid:                  {nx} x {ny}  ({nx * ny} cells)")
    print("  Domain:                [0, 2*pi] x [0, 2*pi]")
    print(f"  Kinematic viscosity nu: {nu}")
    print(f"  Reynolds number Re:    {Re:.2f}")
    print(f"  CFL limit:             {cfl}")
    print(f"  Time step dt:          {dt}")
    print(f"  Steps / Final time:    {steps} / {t_final:.4f}")
    print(f"  Solver used:           {result['solver_name']}")
    print()
    print(f"  L2 error norm:         {l2:.4e}")
    print(f"  Relative L2 error:     {rel_l2 * 100:.2f}%")
    print(f"  Max pointwise error:   {max_err:.4e}")
    print(
        f"  KE decay error:        {dissipation_error:.4e}"
        f"  ({relative_diss_error * 100:.2f}% relative)"
    )
    print()
    print("  VTK files written to examples/output/:")
    print("    tgv_velocity_t0.vtk")
    print("    tgv_velocity_magnitude_t0.vtk")
    print("    tgv_velocity_magnitude_final_numerical.vtk")
    print("    tgv_velocity_analytical_final.vtk")
    print("    tgv_velocity_magnitude_final_analytical.vtk")
    print("    tgv_error_field.vtk")
    print()
    print("Taylor-Green vortex example complete!")


if __name__ == "__main__":
    main()
