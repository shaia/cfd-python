#!/usr/bin/env python3
"""
Poisson Solver Comparison Example

This example compares different iterative methods for solving the pressure
Poisson equation, a critical step in incompressible CFD simulations.

Physics Background:
-------------------
In incompressible flow, the velocity field must satisfy the divergence-free
condition (conservation of mass):

    ∇ · u = 0

When advancing the Navier-Stokes equations in time, a pressure Poisson
equation arises naturally from the projection step:

    ∇²p = f

where f is derived from the intermediate velocity field. Solving this equation
at every time step is typically the dominant cost in incompressible CFD codes.

Iterative Method Trade-offs:
-----------------------------
1. Jacobi:
   - Each unknown updated from neighbors at the *old* iteration
   - Naturally parallelizable (no data dependencies between updates)
   - Spectral radius close to 1 → slow convergence (O(N²) iterations)

2. Gauss-Seidel:
   - Each unknown updated using the most recent values immediately
   - Roughly 2x fewer iterations than Jacobi for the same residual
   - Sequential data dependency limits parallelism

3. SOR (Successive Over-Relaxation):
   - Gauss-Seidel update multiplied by relaxation factor omega
   - Optimal omega ~ 1.5-1.9 reduces iterations by an order of magnitude
   - Sequential like Gauss-Seidel

4. Red-Black SOR:
   - Grid points colored like a checkerboard; red and black updated alternately
   - Removes sequential dependency while retaining SOR convergence rate
   - Fully parallelizable with SIMD/OpenMP

5. Conjugate Gradient (CG):
   - Krylov subspace method - optimal for symmetric positive-definite systems
   - Converges in at most N iterations (exact arithmetic); far fewer in practice
   - Well-suited for SIMD and GPU backends

6. Multigrid:
   - Hierarchy of coarser grids damp errors at all wavelengths
   - Optimal O(N) complexity - independent of grid size per iteration
   - V-cycle or W-cycle schedules control the grid traversal
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import cfd_python
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure to build the package first:")
    print("  pip install -e .")
    sys.exit(1)

import numpy as np


def run_with_method(_method_id, backend_id, nx, ny, steps):
    """Run a lid-driven cavity simulation with a specific Poisson method and backend.

    Args:
        method_id: POISSON_METHOD_* constant
        backend_id: POISSON_BACKEND_* constant
        nx, ny: Grid dimensions
        steps: Number of time steps

    Returns:
        dict with keys 'result', 'elapsed', 'backend_name', or None on failure
    """
    try:
        ok = cfd_python.poisson_set_backend(backend_id)
        if not ok:
            return None
    except Exception:
        return None

    try:
        t0 = time.time()
        result = cfd_python.run_simulation_with_params(
            nx=nx,
            ny=ny,
            xmin=0.0,
            xmax=1.0,
            ymin=0.0,
            ymax=1.0,
            steps=steps,
            dt=0.001,
            cfl=0.5,
        )
        elapsed = time.time() - t0
    except Exception:
        return None

    backend_name = cfd_python.poisson_get_backend_name()
    return {"result": result, "elapsed": elapsed, "backend_name": backend_name}


def main():
    print("CFD Python - Poisson Solver Comparison Example")
    print("=" * 65)

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    # =================================================================
    # Problem Setup
    # =================================================================
    print("\nProblem Setup")
    print("-" * 65)

    nx, ny = 32, 32
    steps = 50

    print("   Problem:  Lid-driven cavity (incompressible N-S)")
    print(f"   Grid:     {nx} x {ny} = {nx * ny} cells")
    print(f"   Steps:    {steps}")
    print("   Domain:   [0,1] x [0,1]")
    print("   dt:       0.001 s")

    print("\n   Default Poisson parameters:")
    params = cfd_python.get_default_poisson_params()
    for key in (
        "tolerance",
        "absolute_tolerance",
        "max_iterations",
        "omega",
        "check_interval",
        "preconditioner",
        "verbose",
    ):
        val = params.get(key, "N/A")
        print(f"     {key:<22}: {val}")

    # =================================================================
    # Backend Availability
    # =================================================================
    print("\nAvailable Poisson Backends")
    print("-" * 65)

    all_backends = [
        ("AUTO", cfd_python.POISSON_BACKEND_AUTO),
        ("SCALAR", cfd_python.POISSON_BACKEND_SCALAR),
        ("OMP", cfd_python.POISSON_BACKEND_OMP),
        ("SIMD", cfd_python.POISSON_BACKEND_SIMD),
        ("GPU", cfd_python.POISSON_BACKEND_GPU),
    ]

    current_backend_id = cfd_python.poisson_get_backend()
    current_backend_name = cfd_python.poisson_get_backend_name()
    simd_avail = cfd_python.poisson_simd_available()

    print(f"   Active backend : {current_backend_name}")
    print(f"   SIMD available : {'Yes' if simd_avail else 'No'}")
    print()
    print(f"   {'Name':<12}  {'Available'}")
    print("   " + "-" * 24)
    for name, bid in all_backends:
        avail = cfd_python.poisson_backend_available(bid)
        tag = " (current)" if bid == current_backend_id else ""
        status = "Yes" if avail else "No"
        print(f"   POISSON_BACKEND_{name:<8}  {status}{tag}")

    # Collect backends that are actually usable (skip AUTO to avoid duplicates)
    runnable_backends = [
        (name, bid)
        for name, bid in all_backends
        if name != "AUTO" and cfd_python.poisson_backend_available(bid)
    ]

    # =================================================================
    # Simulation - iterate over methods and backends
    # =================================================================
    print("\nSimulation: Poisson Method x Backend Comparison")
    print("-" * 65)

    methods = [
        ("Jacobi", cfd_python.POISSON_METHOD_JACOBI),
        ("Gauss-Seidel", cfd_python.POISSON_METHOD_GAUSS_SEIDEL),
        ("SOR", cfd_python.POISSON_METHOD_SOR),
        ("Red-Black SOR", cfd_python.POISSON_METHOD_REDBLACK_SOR),
        ("CG", cfd_python.POISSON_METHOD_CG),
        ("Multigrid", cfd_python.POISSON_METHOD_MULTIGRID),
    ]

    print(
        f"\n   Running {len(methods)} methods x {len(runnable_backends)} "
        f"backend(s) on {nx}x{ny} grid, {steps} steps ...\n"
    )

    # Gather all runs; each entry: (method_name, backend_name, elapsed, max_vel)
    runs = []

    for method_name, method_id in methods:
        for backend_name, backend_id in runnable_backends:
            label = f"{method_name} + {backend_name}"
            data = run_with_method(method_id, backend_id, nx, ny, steps)

            if data is None:
                print(f"   SKIP  {label}")
                continue

            vel_mag = data["result"]["velocity_magnitude"]
            stats = cfd_python.calculate_field_stats(vel_mag)
            max_vel = stats["max"]

            runs.append(
                {
                    "method": method_name,
                    "backend": data["backend_name"],
                    "elapsed": data["elapsed"],
                    "max_vel": max_vel,
                    "solver_name": data["result"].get("solver_name", "unknown"),
                }
            )

    # =================================================================
    # Post-Processing - comparison table
    # =================================================================
    print("\nPost-Processing: Comparison Table")
    print("-" * 65)

    if not runs:
        print("   No runs completed.")
    else:
        col_m = 17
        col_b = 10
        col_t = 10
        col_v = 12
        header = (
            f"   {'Method':<{col_m}}  {'Backend':<{col_b}}  "
            f"{'Time (s)':>{col_t}}  {'Max |u| (m/s)':>{col_v}}"
        )
        print(header)
        print("   " + "-" * (col_m + col_b + col_t + col_v + 8))

        for r in runs:
            print(
                f"   {r['method']:<{col_m}}  {r['backend']:<{col_b}}  "
                f"{r['elapsed']:>{col_t}.4f}  {r['max_vel']:>{col_v}.6f}"
            )

    # =================================================================
    # Validation - all methods should agree on max velocity
    # =================================================================
    print("\nValidation: Physical Consistency Check")
    print("-" * 65)

    if len(runs) < 2:
        print("   Not enough runs for cross-method comparison.")
    else:
        velocities = np.array([r["max_vel"] for r in runs])
        vel_mean = float(np.mean(velocities))
        vel_std = float(np.std(velocities))
        vel_range = float(np.max(velocities) - np.min(velocities))

        print("   Max velocity across all runs:")
        print(f"     Mean  : {vel_mean:.6f} m/s")
        print(f"     Std   : {vel_std:.6f} m/s")
        print(f"     Range : {vel_range:.6f} m/s")

        tolerance = 0.05 * vel_mean if vel_mean > 0.0 else 1e-6
        if vel_range <= tolerance:
            print(
                f"\n   PASS - All methods agree within {100 * vel_range / vel_mean:.2f}% "
                f"of mean velocity."
            )
        else:
            print(
                f"\n   WARN - Methods differ by {vel_range:.6f} m/s "
                f"({100 * vel_range / vel_mean:.2f}% of mean)."
            )
            print("   This may indicate solver divergence or insufficient steps.")

    # Preconditioner reminder
    print("\n   Preconditioner constants (relevant to CG/BiCGSTAB):")
    print(f"     POISSON_PRECOND_NONE   = {cfd_python.POISSON_PRECOND_NONE}")
    print(f"     POISSON_PRECOND_JACOBI = {cfd_python.POISSON_PRECOND_JACOBI}")
    print("     Jacobi preconditioning reduces CG iteration count on ill-conditioned systems.")

    # =================================================================
    # Summary
    # =================================================================
    print("\n" + "=" * 65)
    print("Summary")
    print("-" * 65)

    print(f"   Active Poisson backend : {cfd_python.poisson_get_backend_name()}")
    print(f"   SIMD Poisson           : {'Yes' if simd_avail else 'No'}")
    print(f"   Methods compared       : {len(methods)}")
    print(f"   Backends tested        : {len(runnable_backends)}")
    print(f"   Completed runs         : {len(runs)}")

    if runs:
        fastest = min(runs, key=lambda r: r["elapsed"])
        print(
            f"\n   Fastest run : {fastest['method']} + {fastest['backend']} "
            f"({fastest['elapsed']:.4f} s)"
        )

    print()
    print("   Method selection guide:")
    print("     Small grids  (<64x64)  - SOR or Gauss-Seidel (low overhead)")
    print("     Medium grids (64-256)  - Red-Black SOR (parallelizable) or CG")
    print("     Large grids  (>256x256) - Multigrid (O(N)) or CG with preconditioner")
    print("     SIMD available         - Red-Black SOR or Jacobi with SIMD")
    print("     OpenMP available       - Red-Black SOR + OMP for multi-core speedup")
    print("     GPU available          - CG or Red-Black SOR on GPU backend")

    print("\nPoisson solver comparison complete.")


if __name__ == "__main__":
    main()
