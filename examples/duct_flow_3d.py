#!/usr/bin/env python3
"""
3D Duct Flow Example

Laminar flow in a square cross-section duct driven by a streamwise
pressure gradient - the 3D extension of 2D Poiseuille flow.

Physics Background:
-------------------
In a 2D channel (Poiseuille flow) the velocity profile is parabolic in
the wall-normal direction.  Extending to a square duct with side length H
imposes no-slip on four walls simultaneously, so the profile becomes a
double series in both cross-stream directions (y and z):

    u(y, z) = (16 H^2 dP/dx) / (pi^3 mu)
              * sum_{n=1,3,5,...} (-1)^((n-1)/2) / n^3
              * [1 - cosh(n pi z / H) / cosh(n pi / 2)]
              * cos(n pi y / H)

Key differences from 2D Poiseuille flow:

1. Non-parabolic profile: The corners pull the peak velocity away from
   the theoretical 2D maximum.  For a square duct the maximum occurs at
   the geometric center.

2. Center-to-mean velocity ratio: ~2.096 for a square duct (vs 1.5 for
   2D channel flow).

3. Hydraulic diameter: D_h = H for a square duct, which determines Re.

4. Fully developed state: du/dx = 0 everywhere; u = u(y, z) only.

This example:
- Creates a 3D grid with create_grid (nx=32, ny=16, nz=16)
- Builds a synthetic duct-flow velocity field using the approximation
  u(y, z) proportional to (1 - (2y/H - 1)^2)(1 - (2z/W - 1)^2)
  (product of two parabolas - matches the exact solution well at the
  center while satisfying no-slip exactly on all four walls)
- Demonstrates BC API calls for all four duct walls
- Computes velocity magnitude per 2D slice and cross-section profiles
- Writes 3D VTK files for ParaView visualization
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


def build_duct_velocity(nx, ny, nz, ymin, ymax, zmin, zmax, u_bulk=1.0):
    """Construct an analytical duct-flow velocity field.

    Uses the product-of-parabolas approximation:
        u(y, z) = u_center * f(y) * f(z)
    where f(s) = 1 - (2(s - s_min)/H - 1)^2

    This satisfies no-slip exactly on all four walls and closely
    approximates the double-series solution in the interior.

    The bulk (mean) velocity of f(y)*f(z) over the square [0,H]x[0,H]
    equals (2/3)^2 = 4/9 of the center value, so:
        u_center = u_bulk * (9/4)

    Args:
        nx, ny, nz: Grid dimensions (x is axial; y, z are cross-stream)
        ymin, ymax, zmin, zmax: Cross-section extents
        u_bulk: Target bulk (mean) velocity

    Returns:
        tuple: (u, v, w) as flat Python lists with layout [k, j, i]
    """
    H = ymax - ymin
    W = zmax - zmin

    u_center = u_bulk * (9.0 / 4.0)

    total = nx * ny * nz
    u = [0.0] * total
    v = [0.0] * total
    w = [0.0] * total

    for k in range(nz):
        z = zmin + k * W / max(nz - 1, 1)
        fz = 1.0 - (2.0 * (z - zmin) / W - 1.0) ** 2

        for j in range(ny):
            y = ymin + j * H / max(ny - 1, 1)
            fy = 1.0 - (2.0 * (y - ymin) / H - 1.0) ** 2

            for i in range(nx):
                idx = k * ny * nx + j * nx + i
                u[idx] = u_center * fy * fz
                # v and w stay zero (fully developed, no cross-flow)

    return u, v, w


def apply_duct_noslip(u, nx, ny, nz):
    """Zero axial velocity on all four duct walls (conceptual demonstration).

    In a fully developed duct the solver operates on 2D (y, z) slices.
    bc_apply_noslip is called once per slice to enforce the no-slip
    condition on the top and bottom walls (y direction); the front and
    back walls (z direction) are represented by the BC_EDGE_FRONT and
    BC_EDGE_BACK constants.

    For the synthetic field the walls are already zero by construction
    (parabola evaluates to zero at the boundaries).  These calls show
    the API pattern a real simulation would use.

    Args:
        u: Flat velocity list (layout [k, j, i])
        nx, ny, nz: Grid dimensions
    """
    slice_size = nx * ny

    for k in range(nz):
        # Extract u-slice for this z-station
        u_slice = u[k * slice_size : (k + 1) * slice_size]
        v_slice = [0.0] * slice_size

        # Apply no-slip on top/bottom walls (y-direction) for every slice
        cfd_python.bc_apply_noslip(u_slice, v_slice, nx, ny)

        # Front and back walls (z = zmin, z = zmax): zero entire slice.
        # The 2D BC functions operate on (x,y) planes, so we enforce the
        # z-boundary no-slip manually by zeroing the first and last slices.
        if k == 0 or k == nz - 1:
            for idx in range(slice_size):
                u_slice[idx] = 0.0
                v_slice[idx] = 0.0

        # Write enforced slice back (walls were already zero; this is the
        # correct pattern for a live simulation)
        u[k * slice_size : (k + 1) * slice_size] = u_slice


def slice_velocity_magnitude(u, nx, ny, _nz, k):
    """Compute velocity magnitude for a single z-slice.

    Args:
        u: Full 3D flat velocity list
        nx, ny, nz: Grid dimensions
        k: z-index of the slice

    Returns:
        list: velocity_magnitude for the slice (length nx*ny)
    """
    slice_size = nx * ny
    u_slice = u[k * slice_size : (k + 1) * slice_size]
    v_slice = [0.0] * slice_size
    return cfd_python.compute_velocity_magnitude(u_slice, v_slice, nx, ny)


def main():
    print("CFD Python - 3D Duct Flow Example")
    print("=" * 60)

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    # =================================================================
    # Problem Setup
    # =================================================================
    print("\nProblem Setup")
    print("-" * 60)

    # Grid: x is axial (flow direction); y and z are cross-stream
    nx, ny, nz = 32, 16, 16

    xmin, xmax = 0.0, 2.0  # Duct length = 2 m
    ymin, ymax = 0.0, 1.0  # Duct height H = 1 m
    zmin, zmax = 0.0, 1.0  # Duct width  W = 1 m  (square cross-section)

    H = ymax - ymin
    W = zmax - zmin

    # Flow parameters
    u_bulk = 1.0  # bulk (mean) axial velocity [m/s]
    nu = 1e-3  # kinematic viscosity [m^2/s]  (water-like)
    D_h = H  # hydraulic diameter = H for a square duct

    Re = u_bulk * D_h / nu

    print(f"  Grid:              {nx} x {ny} x {nz}  (axial x height x width)")
    print(f"  Duct length:       {xmax - xmin:.1f} m")
    print(f"  Cross-section:     {H:.1f} m x {W:.1f} m  (square)")
    print(f"  Hydraulic diam.:   {D_h:.3f} m")
    print(f"  Bulk velocity:     {u_bulk:.3f} m/s")
    print(f"  Kinematic visc.:   {nu:.2e} m^2/s")
    print(f"  Reynolds number:   {Re:.1f}  (laminar: Re < 2300)")

    # Backend info
    print(f"\n  SIMD backend:      {cfd_python.get_simd_name()}")
    print(f"  BC backend:        {cfd_python.bc_get_backend_name()}")

    # 3D grid object
    grid = cfd_python.create_grid(
        nx=nx,
        ny=ny,
        xmin=xmin,
        xmax=xmax,
        ymin=ymin,
        ymax=ymax,
        nz=nz,
        zmin=zmin,
        zmax=zmax,
    )

    print(f"\n  Grid created:      {grid['nx']} x {grid['ny']} x {grid.get('nz', 1)}")
    print(f"  Total cells:       {nx * ny * nz:,}")

    # =================================================================
    # Simulation - build synthetic duct-flow field
    # =================================================================
    print("\nSimulation")
    print("-" * 60)

    print("  Building analytical duct-flow velocity field...")
    u, v, w = build_duct_velocity(nx, ny, nz, ymin, ymax, zmin, zmax, u_bulk)

    print("  Applying no-slip boundary conditions on all four walls...")
    apply_duct_noslip(u, nx, ny, nz)

    # Global velocity field statistics
    u_arr = np.array(u)
    u_max = float(u_arr.max())
    u_mean_nonzero = float(u_arr[u_arr > 0].mean()) if (u_arr > 0).any() else 0.0

    print(f"  Axial velocity range:  [{u_arr.min():.6f}, {u_max:.6f}] m/s")
    print(f"  Mean (interior) u:     {u_mean_nonzero:.6f} m/s")

    # =================================================================
    # Post-Processing
    # =================================================================
    print("\nPost-Processing")
    print("-" * 60)

    # Velocity magnitude slices at selected z-stations
    z_stations = [0, nz // 4, nz // 2, 3 * nz // 4, nz - 1]
    z_labels = ["z=zmin (wall)", "z=W/4", "z=W/2 (center)", "z=3W/4", "z=zmax (wall)"]

    print("\n  Velocity magnitude statistics per z-slice:")
    print(f"  {'Slice':>5}  {'Label':>18}  {'Min':>10}  {'Max':>10}  {'Avg':>10}")
    print("  " + "-" * 60)

    for k, label in zip(z_stations, z_labels):
        vel_mag = slice_velocity_magnitude(u, nx, ny, nz, k)
        stats = cfd_python.calculate_field_stats(vel_mag)
        print(
            f"  {k:5d}  {label:>18}  {stats['min']:10.6f}"
            f"  {stats['max']:10.6f}  {stats['avg']:10.6f}"
        )

    # Cross-section profile at z = W/2 (center slice)
    k_center = nz // 2
    i_center = nx // 2
    slice_size = nx * ny

    print("\n  Axial velocity profile u(y) at z=W/2, x=L/2 (center cut):")
    print(f"  {'j':>4}  {'y [m]':>8}  {'u [m/s]':>10}  {'u/u_bulk':>10}")
    print("  " + "-" * 38)

    for j in range(0, ny, max(1, ny // 8)):
        y = ymin + j * H / max(ny - 1, 1)
        idx = k_center * slice_size + j * nx + i_center
        u_val = u[idx]
        print(f"  {j:4d}  {y:8.4f}  {u_val:10.6f}  {u_val / u_bulk:10.6f}")

    # Profile in z-direction at y = H/2 (center height)
    j_center = ny // 2

    print("\n  Axial velocity profile u(z) at y=H/2, x=L/2 (center cut):")
    print(f"  {'k':>4}  {'z [m]':>8}  {'u [m/s]':>10}  {'u/u_bulk':>10}")
    print("  " + "-" * 38)

    for k in range(0, nz, max(1, nz // 8)):
        z = zmin + k * W / max(nz - 1, 1)
        idx = k * slice_size + j_center * nx + i_center
        u_val = u[idx]
        print(f"  {k:4d}  {z:8.4f}  {u_val:10.6f}  {u_val / u_bulk:10.6f}")

    # =================================================================
    # Validation
    # =================================================================
    print("\nValidation")
    print("-" * 60)

    # Center velocity from the field
    idx_center = k_center * slice_size + j_center * nx + i_center
    u_center_computed = u[idx_center]

    # Theoretical center-to-bulk ratio for a square duct
    # Exact double-series result: u_max / u_bulk ~= 2.096
    ratio_theory = 2.096
    ratio_computed = u_center_computed / u_bulk

    # Our product-of-parabolas model gives u_center = (9/4) * u_bulk = 2.25
    # (slightly above the exact 2.096 because the double-series rounds the
    # peak more than two independent parabolas do)
    print(f"  Center velocity:          {u_center_computed:.6f} m/s")
    print(f"  Bulk velocity:            {u_bulk:.6f} m/s")
    print(f"  Computed u_max / u_bulk:  {ratio_computed:.4f}")
    print(f"  Exact (double series):    {ratio_theory:.4f}")
    print(f"  Model (product parabola): {9.0 / 4.0:.4f}")
    print("  2D Poiseuille reference:  1.5000")

    # Wall no-slip check: corners and edges should be zero
    corners = [
        (0, 0, 0),  # bottom-front-left
        (0, ny - 1, 0),  # top-front-left
        (0, 0, nz - 1),  # bottom-back-left
        (0, ny - 1, nz - 1),  # top-back-left
    ]
    print("\n  No-slip check (u at corners/wall nodes should be 0):")
    all_zero = True
    for i, j, k in corners:
        idx = k * slice_size + j * nx + i
        val = u[idx]
        ok = abs(val) < 1e-12
        if not ok:
            all_zero = False
        print(f"    (i={i}, j={j}, k={k}): u = {val:.2e}  {'OK' if ok else 'FAIL'}")

    print(f"\n  No-slip condition satisfied: {all_zero}")

    # =================================================================
    # VTK Output - write 3D fields for ParaView
    # =================================================================
    print("\nVTK Output")
    print("-" * 60)

    # 3D axial velocity (scalar)
    vtk_u = os.path.join(output_dir, "duct_flow_u.vtk")
    cfd_python.write_vtk_scalar(
        filename=vtk_u,
        field_name="axial_velocity",
        data=u,
        nx=nx,
        ny=ny,
        xmin=xmin,
        xmax=xmax,
        ymin=ymin,
        ymax=ymax,
        nz=nz,
        zmin=zmin,
        zmax=zmax,
    )
    print(f"  Wrote: output/duct_flow_u.vtk  ({nx * ny * nz} points)")

    # 3D velocity vector (u, v, w)
    vtk_vel = os.path.join(output_dir, "duct_flow_velocity.vtk")
    cfd_python.write_vtk_vector(
        filename=vtk_vel,
        field_name="velocity",
        u_data=u,
        v_data=v,
        nx=nx,
        ny=ny,
        xmin=xmin,
        xmax=xmax,
        ymin=ymin,
        ymax=ymax,
        w_data=w,
        nz=nz,
        zmin=zmin,
        zmax=zmax,
    )
    print(f"  Wrote: output/duct_flow_velocity.vtk  ({nx * ny * nz} points)")

    # 3D velocity magnitude (computed per z-slice, assembled into full volume)
    mag_3d = []
    for k in range(nz):
        vm = slice_velocity_magnitude(u, nx, ny, nz, k)
        mag_3d.extend(vm)

    vtk_mag = os.path.join(output_dir, "duct_flow_magnitude.vtk")
    cfd_python.write_vtk_scalar(
        filename=vtk_mag,
        field_name="velocity_magnitude",
        data=mag_3d,
        nx=nx,
        ny=ny,
        xmin=xmin,
        xmax=xmax,
        ymin=ymin,
        ymax=ymax,
        nz=nz,
        zmin=zmin,
        zmax=zmax,
    )
    print(f"  Wrote: output/duct_flow_magnitude.vtk  ({len(mag_3d)} points)")

    # =================================================================
    # Summary
    # =================================================================
    print("\n" + "=" * 60)
    print("Summary")
    print("-" * 60)
    print(f"  Duct geometry:      {H:.1f} m x {W:.1f} m square cross-section")
    print(f"  Duct length:        {xmax - xmin:.1f} m")
    print(f"  Grid:               {nx} x {ny} x {nz}  ({nx * ny * nz:,} cells)")
    print(f"  Reynolds number:    {Re:.1f}  (flow is laminar)")
    print(
        f"  u_max / u_bulk:     {ratio_computed:.4f}  (exact: {ratio_theory:.4f}, 2D ref: 1.5000)"
    )
    print()
    print("  VTK files (open in ParaView):")
    print("    output/duct_flow_u.vtk          - axial velocity scalar")
    print("    output/duct_flow_velocity.vtk   - velocity vector field")
    print("    output/duct_flow_magnitude.vtk  - velocity magnitude scalar")
    print()
    print("  ParaView tips:")
    print("    - Use Slice filter to view y-z cross-sections")
    print("    - Apply 'Glyph' filter on vector file for arrow plots")
    print("    - Use 'Plot Over Line' for wall-normal profiles")
    print()
    print("3D duct flow example complete!")


if __name__ == "__main__":
    main()
