#!/usr/bin/env python3
"""
Grid Convergence Study

Formal verification that CFD results are independent of grid resolution.
Mesh refinement studies are required before trusting any simulation result.

Physics Background:
-------------------
Numerical discretization introduces truncation error that scales as O(h^p),
where h is the grid spacing and p is the formal order of accuracy. For a
second-order scheme (central differences), p = 2: halving the grid spacing
reduces the error by a factor of four.

A grid convergence study runs the same physical problem on a sequence of
progressively finer grids. Observed convergence order is computed between
successive refinement levels:

    p_obs = log(||e_coarse|| / ||e_fine||) / log(r)

where r is the refinement ratio (h_coarse / h_fine) and ||e|| is the L2
error norm against a reference solution. For a sequence of three grids, the
Grid Convergence Index (GCI) provides a formal uncertainty estimate:

    GCI = F_s * |e_relative| / (r^p - 1)

where F_s = 1.25 is a safety factor recommended by Roache (1994).

Test Problem: Lid-Driven Cavity
--------------------------------
The lid-driven cavity is the standard CFD verification benchmark. A unit
square cavity is filled with fluid; the top wall moves at unit velocity,
driving a primary recirculating vortex. Because no analytical solution exists
for the full viscous problem, the finest grid in the study acts as the
reference solution - the classical approach for problems with no closed form.

Reference: Ghia, Ghia & Shin (1982), J. Comput. Phys. 48, 387-411.
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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_cavity_level(n, steps, dt=0.001, cfl=0.2):
    """Run one grid level of the lid-driven cavity.

    Args:
        n: Grid dimension (n x n square grid)
        steps: Number of time steps
        dt: Time step size
        cfl: CFL number

    Returns:
        dict returned by run_simulation_with_params
    """
    return cfd_python.run_simulation_with_params(
        nx=n,
        ny=n,
        xmin=0.0,
        xmax=1.0,
        ymin=0.0,
        ymax=1.0,
        steps=steps,
        dt=dt,
        cfl=cfl,
    )


def interpolate_to_fine(coarse_data, n_coarse, n_fine):
    """Bilinear interpolation of a coarse field onto the fine grid.

    Both grids span the unit square [0,1]x[0,1]. The coarse field is
    represented as a flat row-major array (length n_coarse^2); the returned
    array has length n_fine^2.

    Args:
        coarse_data: Flat list or array of length n_coarse * n_coarse
        n_coarse: Coarse grid dimension
        n_fine: Fine grid dimension

    Returns:
        numpy array of length n_fine * n_fine
    """
    coarse = np.array(coarse_data, dtype=np.float64).reshape(n_coarse, n_coarse)

    # Coordinate vectors for each grid (cell-centred at nodes here, i.e. 0..1)
    x_coarse = np.linspace(0.0, 1.0, n_coarse)
    y_coarse = np.linspace(0.0, 1.0, n_coarse)
    x_fine = np.linspace(0.0, 1.0, n_fine)
    y_fine = np.linspace(0.0, 1.0, n_fine)

    # Build fine grid via bilinear interpolation (numpy only)
    fine = np.zeros((n_fine, n_fine), dtype=np.float64)

    for j_f, y in enumerate(y_fine):
        # Find coarse bracket in y
        iy = np.searchsorted(y_coarse, y, side="right") - 1
        iy = int(np.clip(iy, 0, n_coarse - 2))
        ty = (y - y_coarse[iy]) / (y_coarse[iy + 1] - y_coarse[iy])

        for i_f, x in enumerate(x_fine):
            # Find coarse bracket in x
            ix = np.searchsorted(x_coarse, x, side="right") - 1
            ix = int(np.clip(ix, 0, n_coarse - 2))
            tx = (x - x_coarse[ix]) / (x_coarse[ix + 1] - x_coarse[ix])

            # Bilinear blend
            fine[j_f, i_f] = (1.0 - ty) * (
                (1.0 - tx) * coarse[iy, ix] + tx * coarse[iy, ix + 1]
            ) + ty * ((1.0 - tx) * coarse[iy + 1, ix] + tx * coarse[iy + 1, ix + 1])

    return fine.ravel()


def l2_error(field, reference):
    """Compute the discrete L2 error norm.

    ||e||_2 = sqrt( sum((u_h - u_ref)^2) / N )

    Args:
        field: numpy array, approximation
        reference: numpy array, reference solution (same size)

    Returns:
        float: L2 norm of the pointwise difference
    """
    diff = np.asarray(field, dtype=np.float64) - np.asarray(reference, dtype=np.float64)
    return float(np.sqrt(np.mean(diff**2)))


def observed_order(e_coarse, e_fine, r=2.0):
    """Compute observed order of convergence from two successive error norms.

    p = log(e_coarse / e_fine) / log(r)

    Args:
        e_coarse: L2 error on the coarser grid
        e_fine: L2 error on the finer grid
        r: Refinement ratio (default 2)

    Returns:
        float: observed order p, or NaN if either error is zero
    """
    if e_coarse <= 0.0 or e_fine <= 0.0:
        return float("nan")
    return float(np.log(e_coarse / e_fine) / np.log(r))


def gci(e_relative, p_obs, r=2.0, fs=1.25):
    """Grid Convergence Index (Roache 1994).

    GCI = F_s * |e_rel| / (r^p - 1)

    Args:
        e_relative: Relative error between two adjacent grid levels
        p_obs: Observed order of convergence
        r: Refinement ratio (default 2)
        fs: Safety factor (default 1.25 for three or more grids)

    Returns:
        float: GCI as a fraction (multiply by 100 for percent)
    """
    denom = r**p_obs - 1.0
    if denom <= 0.0:
        return float("nan")
    return fs * abs(e_relative) / denom


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print("CFD Python - Grid Convergence Study")
    print("=" * 60)

    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Problem Setup
    # ------------------------------------------------------------------
    print("\nProblem Setup")
    print("-" * 60)

    grid_sizes = [16, 32, 64, 128]
    refinement_ratio = 2  # each level doubles resolution in each direction
    base_steps = 200  # steps for the coarsest grid
    dt = 0.001
    cfl = 0.2

    print("  Test problem : Lid-driven cavity (unit square, Re ~ 100)")
    print(f"  Grid levels  : {grid_sizes}")
    print(f"  Refinement   : r = {refinement_ratio} (factor {refinement_ratio}x each direction)")
    print(f"  Base steps   : {base_steps} (scaled proportionally per level)")
    print(f"  dt           : {dt},  CFL : {cfl}")

    # Show backend
    print(f"\n  SIMD backend : {cfd_python.get_simd_name()}")
    print(f"  BC backend   : {cfd_python.bc_get_backend_name()}")

    # ------------------------------------------------------------------
    # Simulation - run all grid levels
    # ------------------------------------------------------------------
    print("\nSimulation")
    print("-" * 60)

    level_results = []  # list of dicts: {n, steps, vel_mag, stats}

    for level, n in enumerate(grid_sizes):
        # Scale steps proportionally so physical time is comparable and
        # finer grids have sufficient resolution to reach the same state.
        steps = base_steps * (refinement_ratio**level)
        h = 1.0 / (n - 1)

        print(f"\n  Level {level}: {n}x{n} grid  (h = {h:.5f},  steps = {steps})")

        result = run_cavity_level(n, steps, dt=dt, cfl=cfl)

        vel_mag = result["velocity_magnitude"]
        vel_mag_arr = np.array(vel_mag, dtype=np.float64)

        # Create the grid descriptor (demonstrates create_grid API)
        _ = cfd_python.create_grid(n, n, 0.0, 1.0, 0.0, 1.0)

        # Field statistics via the library API
        stats = cfd_python.calculate_field_stats(vel_mag)

        print(f"    Solver     : {result['solver_name']}")
        print(f"    vel_mag max: {stats['max']:.6f}")
        print(f"    vel_mag avg: {stats['avg']:.6f}")

        level_results.append(
            {
                "n": n,
                "h": h,
                "steps": steps,
                "vel_mag": vel_mag_arr,
                "stats": stats,
                "solver_name": result["solver_name"],
            }
        )

    # ------------------------------------------------------------------
    # Post-Processing - interpolate to finest grid and compute L2 errors
    # ------------------------------------------------------------------
    print("\nPost-Processing")
    print("-" * 60)

    n_fine = grid_sizes[-1]
    ref_field = level_results[-1]["vel_mag"]  # finest grid is the reference

    errors = []  # L2 error for each level (finest grid has error = 0 by definition)

    for rec in level_results:
        n = rec["n"]
        if n == n_fine:
            errors.append(0.0)
            continue

        interpolated = interpolate_to_fine(rec["vel_mag"], n, n_fine)
        e = l2_error(interpolated, ref_field)
        errors.append(e)
        print(f"  L2 error  {n:3d}x{n:<3d} vs {n_fine}x{n_fine}: {e:.6e}")

    # ------------------------------------------------------------------
    # Validation - convergence table and GCI
    # ------------------------------------------------------------------
    print("\nValidation")
    print("-" * 60)

    print(f"\n  {'Grid':>8}  {'h':>10}  {'L2 error':>12}  {'Conv. rate':>12}  {'GCI (%)':>10}")
    print("  " + "-" * 60)

    p_values = []
    gci_values = []

    for i, (rec, e) in enumerate(zip(level_results, errors)):
        n = rec["n"]
        h = rec["h"]

        if i == 0:
            # No coarser level to compare with
            p_str = "       n/a"
            gci_str = "       n/a"
        elif i == len(level_results) - 1:
            # Finest grid is the reference; error is zero by construction
            p_str = "       ref"
            gci_str = "       ref"
        else:
            e_prev = errors[i - 1]
            p_obs = observed_order(e_prev, e, r=refinement_ratio)
            p_values.append(p_obs)

            # Relative error for GCI: normalised by the finer level's value
            ref_norm = float(np.sqrt(np.mean(ref_field**2)))
            e_rel = e / ref_norm if ref_norm > 0.0 else float("nan")
            gci_val = gci(e_rel, p_obs, r=refinement_ratio)
            gci_values.append(gci_val * 100.0)

            p_str = f"{p_obs:10.3f}"
            gci_str = f"{gci_val * 100.0:10.3f}"

        e_str = f"{e:.6e}" if e > 0.0 else "  (reference)"
        print(f"  {n:3d}x{n:<3d}  {h:10.5f}  {e_str:>12}  {p_str:>12}  {gci_str:>10}")

    # Expected vs observed order
    print()
    if p_values:
        p_mean = float(np.mean(p_values))
        print("  Expected convergence order : 2.00  (second-order scheme)")
        print(f"  Observed mean order        : {p_mean:.3f}")

        if abs(p_mean - 2.0) < 0.5:
            verdict = "PASS - within 0.5 of expected second-order convergence"
        else:
            verdict = "WARN - observed order deviates more than 0.5 from second-order"
        print(f"  Convergence check          : {verdict}")

    if gci_values:
        gci_finest = gci_values[-1]
        print(f"\n  GCI on finest interior level : {gci_finest:.3f}%")
        if gci_finest < 5.0:
            print("  Uncertainty estimate         : acceptable (< 5%)")
        else:
            print("  Uncertainty estimate         : elevated - consider further refinement")

    # Richardson extrapolation for the finest interior pair (64 -> 128 reference)
    idx_fine = len(grid_sizes) - 2  # 64-grid index
    idx_finer = len(grid_sizes) - 1  # 128-grid (reference)
    if len(p_values) >= 1 and errors[idx_fine] > 0.0:
        p_rich = p_values[-1]
        r_rich = refinement_ratio
        f_fine = float(np.mean(level_results[idx_fine]["vel_mag"]))
        f_finer = float(np.mean(level_results[idx_finer]["vel_mag"]))
        # Richardson extrapolated value
        f_extrap = f_finer + (f_finer - f_fine) / (r_rich**p_rich - 1.0)
        print("\n  Richardson extrapolation (mean vel_mag):")
        print(f"    {grid_sizes[idx_fine]:3d}x{grid_sizes[idx_fine]:<3d} grid : {f_fine:.6f}")
        print(f"    {grid_sizes[idx_finer]:3d}x{grid_sizes[idx_finer]:<3d} grid : {f_finer:.6f}")
        print(f"    Extrapolated       : {f_extrap:.6f}")

    # Per-level field statistics table
    print("\n  Per-level field statistics:")
    print(f"  {'Grid':>8}  {'vel_max':>10}  {'vel_avg':>10}  {'vel_min':>10}")
    print("  " + "-" * 44)
    for rec in level_results:
        n = rec["n"]
        s = rec["stats"]
        print(f"  {n:3d}x{n:<3d}  {s['max']:10.6f}  {s['avg']:10.6f}  {s['min']:10.6f}")

    # ------------------------------------------------------------------
    # VTK output - finest grid
    # ------------------------------------------------------------------
    print("\nWriting VTK output for finest grid...")

    finest = level_results[-1]
    n_vtk = finest["n"]
    vel_mag_list = finest["vel_mag"].tolist()

    vtk_path = os.path.join(output_dir, f"grid_convergence_{n_vtk}x{n_vtk}.vtk")
    cfd_python.write_vtk_scalar(
        vtk_path,
        "velocity_magnitude",
        vel_mag_list,
        n_vtk,
        n_vtk,
        0.0,
        1.0,
        0.0,
        1.0,
    )
    print(f"  Written: {vtk_path}")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("Grid Convergence Study - Summary")
    print("=" * 60)
    print(f"\n  Grid levels run  : {[f'{n}x{n}' for n in grid_sizes]}")
    print(f"  Reference grid   : {n_fine}x{n_fine}")
    if p_values:
        print(f"  Mean conv. order : {float(np.mean(p_values)):.3f}  (target: 2.00)")
    if gci_values:
        print(f"  GCI finest level : {gci_values[-1]:.3f}%")
    print(f"\n  VTK output       : output/grid_convergence_{n_fine}x{n_fine}.vtk")
    print("\nGrid convergence study complete.")


if __name__ == "__main__":
    main()
