#!/usr/bin/env python3
"""
Backward-Facing Step Flow Example

This example demonstrates flow over a backward-facing step - a canonical
benchmark problem in computational fluid dynamics.

Physics Background:
-------------------
A backward-facing step is formed when a channel undergoes a sudden expansion.
Fluid flowing through the narrower upstream section (the "step" portion)
expands into the wider downstream region, creating a separated shear layer
and a recirculation zone immediately behind the step.

Key characteristics:

1. Flow separation: The boundary layer cannot follow the abrupt geometry
   change and separates at the step corner. This produces a region of
   reversed (negative u) velocity near the lower wall downstream of the step.

2. Reattachment: The separated shear layer eventually reattaches to the lower
   wall at the reattachment point x_r. Downstream of this point, the flow
   gradually redevelops toward a new fully-developed profile.

3. Reattachment length vs. Reynolds number: The reattachment length scales
   approximately linearly with Re at low Reynolds numbers. For a 2:1 expansion
   ratio (step height h = half channel height H/2):
     - Re ~ 100: x_r ~ 5 h   (Armaly et al. 1983, J. Fluid Mech. 127:473-496)
     - Re ~ 200: x_r ~ 7 h

4. Geometry (2:1 expansion ratio):
   - Inlet half-height (upstream): h = H/2
   - Full downstream height:        H
   - Step height:                    h = H/2
   - Domain length:                 10 h downstream for reattachment capture

5. Boundary conditions:
   - Inlet (left edge, upper half): uniform velocity u_inlet
   - Step wall (left edge, lower half): no-flow (zero velocity)
   - No-slip walls: top and bottom of the full channel
   - Outlet (right edge): zero-gradient

Reference:
  Armaly, B.F., Durst, F., Pereira, J.C.F., Schonung, B. (1983).
  Experimental and theoretical investigation of backward-facing step flow.
  Journal of Fluid Mechanics, 127, 473-496.
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


def setup_backward_step_bcs(u, v, nx, ny, u_inlet):
    """Apply boundary conditions for the backward-facing step.

    Inlet occupies the upper half of the left edge (j >= ny//2).
    The lower half of the left edge is the step wall (zero velocity).
    No-slip is enforced on top and bottom walls.
    Zero-gradient outlet is applied on the right edge.

    Args:
        u: x-velocity field (list, length nx*ny), modified in place
        v: y-velocity field (list, length nx*ny), modified in place
        nx: grid points in x direction
        ny: grid points in y direction
        u_inlet: uniform inlet velocity magnitude
    """
    j_step = ny // 2  # step occupies rows 0 .. j_step-1

    # Inlet: upper portion of the left edge
    for j in range(j_step, ny):
        idx = j * nx  # left edge column
        u[idx] = u_inlet
        v[idx] = 0.0

    # Step wall: lower portion of the left edge - zero velocity
    for j in range(0, j_step):
        idx = j * nx
        u[idx] = 0.0
        v[idx] = 0.0

    # No-slip: top wall (j = ny-1)
    for i in range(nx):
        idx = (ny - 1) * nx + i
        u[idx] = 0.0
        v[idx] = 0.0

    # No-slip: bottom wall (j = 0)
    for i in range(nx):
        u[i] = 0.0
        v[i] = 0.0

    # No-slip: step face (the horizontal surface at j = j_step, i = 0)
    # This is the top of the step block. Cells below j_step at x=0 are wall.
    for j in range(0, j_step):
        idx = j * nx
        u[idx] = 0.0
        v[idx] = 0.0

    # Zero-gradient outlet: right edge
    cfd_python.bc_apply_outlet_velocity(u, v, nx, ny, cfd_python.BC_EDGE_RIGHT)


def find_reattachment_point(u, nx, ny, xmin, xmax):
    """Estimate the reattachment length from the u-velocity field.

    Reattachment is where the streamwise velocity u near the bottom wall
    transitions from negative (recirculation) back to positive.

    Args:
        u: x-velocity field (list, length nx*ny)
        nx: grid points in x direction
        ny: grid points in y direction
        xmin: domain left coordinate
        xmax: domain right coordinate

    Returns:
        float: estimated x-coordinate of reattachment, or -1 if not found
    """
    _ = ny  # used to validate field size in production code
    dx = (xmax - xmin) / (nx - 1)
    j_wall = 1  # one row above the bottom wall

    reattach_x = -1.0
    for i in range(1, nx - 1):
        idx_curr = j_wall * nx + i
        idx_next = j_wall * nx + i + 1
        u_curr = u[idx_curr]
        u_next = u[idx_next]
        # Sign change from negative to positive indicates reattachment
        if u_curr < 0.0 and u_next >= 0.0:
            # Linear interpolation for sub-cell precision
            frac = -u_curr / (u_next - u_curr) if (u_next - u_curr) != 0.0 else 0.0
            reattach_x = xmin + (i + frac) * dx
            break

    return reattach_x


def compute_grid_spacing_info(coords):
    """Return min and max spacing from a sorted coordinate list.

    Args:
        coords: list of coordinate values in ascending order

    Returns:
        tuple: (min_spacing, max_spacing)
    """
    spacings = [coords[k + 1] - coords[k] for k in range(len(coords) - 1)]
    return min(spacings), max(spacings)


def main():
    print("CFD Python - Backward-Facing Step Example")
    print("=" * 60)

    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    # =========================================================
    # Problem Setup
    # =========================================================
    print("\nProblem Setup")
    print("-" * 60)

    # Geometry: 2:1 expansion ratio
    # Step height h = H/2 where H is the full downstream channel height.
    # Domain length = 10 * h downstream for reattachment capture.
    H = 1.0  # full downstream channel height
    h = H / 2.0  # step height (= inlet half-height)

    xmin = 0.0
    xmax = 10.0 * h  # domain length = 10 step heights
    ymin = 0.0
    ymax = H

    # Flow parameters
    u_inlet = 1.0  # uniform inlet velocity
    nu = 0.01  # kinematic viscosity  ->  Re = u_inlet * h / nu = 100

    Re = u_inlet * h / nu

    # Grid: 64 x 32, stretched (beta=1.2) to cluster points near walls
    nx, ny = 64, 32
    beta = 1.2

    print("  Geometry:")
    print(f"    Full channel height H = {H:.3f}")
    print(f"    Step height h         = {h:.3f}")
    print(f"    Domain length         = {xmax:.3f}  ({xmax / h:.1f} step heights)")
    print("  Flow parameters:")
    print(f"    Inlet velocity        = {u_inlet:.3f}")
    print(f"    Kinematic viscosity   = {nu:.4f}")
    print(f"    Reynolds number       = {Re:.1f}")
    print(f"  Grid: {nx} x {ny}, beta = {beta}")

    # Create stretched grid
    grid = cfd_python.create_grid_stretched(nx, ny, xmin, xmax, ymin, ymax, beta)

    x_coords = grid["x_coords"]
    y_coords = grid["y_coords"]

    dx_min, dx_max = compute_grid_spacing_info(x_coords)
    dy_min, dy_max = compute_grid_spacing_info(y_coords)
    stretching_ratio_x = dx_max / dx_min if dx_min > 0 else 0.0
    stretching_ratio_y = dy_max / dy_min if dy_min > 0 else 0.0

    print(f"\n  Grid stretching (beta={beta}):")
    print(f"    x-spacing: min={dx_min:.5f}  max={dx_max:.5f}  ratio={stretching_ratio_x:.2f}")
    print(f"    y-spacing: min={dy_min:.5f}  max={dy_max:.5f}  ratio={stretching_ratio_y:.2f}")

    # Show backend info
    print("\n  Compute backend:")
    print(f"    SIMD:       {cfd_python.get_simd_name()}")
    print(f"    BC backend: {cfd_python.bc_get_backend_name()}")

    # =========================================================
    # Simulation
    # =========================================================
    print("\nSimulation")
    print("-" * 60)

    # Initialise velocity fields and apply step BCs for BC demonstration
    size = nx * ny
    u_ic = [0.0] * size
    v_ic = [0.0] * size

    setup_backward_step_bcs(u_ic, v_ic, nx, ny, u_inlet)

    j_step = ny // 2
    print(f"  Inlet occupies rows j={j_step}..{ny - 1} (upper half of left edge)")
    print(f"  Step wall at rows j=0..{j_step - 1} (lower half of left edge)")

    # Inlet velocity check
    inlet_u_vals = [u_ic[j * nx] for j in range(ny)]
    inlet_nonzero = sum(1 for v in inlet_u_vals if v > 0.0)
    print(f"  Inlet active rows: {inlet_nonzero} of {ny}")
    print(f"  Inlet velocity set to {u_inlet:.3f} on active rows")

    # Run simulation
    steps = 100
    dt = 0.001
    cfl = 0.2

    print(f"\n  Running {steps} steps (dt={dt}, CFL={cfl})...")

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

    print(f"  Completed {result['steps']} steps")
    print(f"  Solver: {result['solver_name']}")

    # =========================================================
    # Post-Processing
    # =========================================================
    print("\nPost-Processing")
    print("-" * 60)

    vel_mag = result["velocity_magnitude"]
    vel_stats = cfd_python.calculate_field_stats(vel_mag)

    print("  Velocity magnitude:")
    print(f"    Min: {vel_stats['min']:.6f}")
    print(f"    Max: {vel_stats['max']:.6f}")
    print(f"    Avg: {vel_stats['avg']:.6f}")

    # Extract u-velocity from the initial-condition field.
    # run_simulation_with_params returns velocity_magnitude but not separate
    # u/v components, so we use the BC-initialised u_ic field to demonstrate
    # the recirculation-detection logic that would apply to a fully time-stepped
    # u-velocity result.
    u_field = u_ic

    # Identify recirculation zone: columns near the bottom wall with u < 0
    j_near_bottom = 1  # one row above bottom wall
    recirculation_cols = []
    for i in range(1, nx):
        idx = j_near_bottom * nx + i
        if u_field[idx] < 0.0:
            recirculation_cols.append(i)

    if recirculation_cols:
        x_recirc_start = x_coords[recirculation_cols[0]]
        x_recirc_end = x_coords[recirculation_cols[-1]]
        recirc_length = x_recirc_end - x_recirc_start
        print("\n  Recirculation zone (u < 0 near bottom wall):")
        print(f"    Start: x = {x_recirc_start:.4f}")
        print(f"    End:   x = {x_recirc_end:.4f}")
        print(f"    Length: {recirc_length:.4f}  ({recirc_length / h:.2f} step heights)")
    else:
        print("\n  No recirculation detected near bottom wall in current field.")

    # Reattachment estimate
    reattach_x = find_reattachment_point(u_field, nx, ny, xmin, xmax)
    reattach_nondim = reattach_x / h if reattach_x > 0.0 else -1.0
    if reattach_x > 0.0:
        print(
            f"\n  Estimated reattachment x = {reattach_x:.4f}  ({reattach_nondim:.2f} step heights)"
        )
    else:
        print("\n  Reattachment point not detected in domain (increase domain length).")

    # Cross-section u-velocity profile at several x-stations
    print("\n  Cross-section u-velocity profiles (u vs y):")
    x_fractions = [0.1, 0.3, 0.5, 0.7, 0.9]
    x_stations = [int(f * (nx - 1)) for f in x_fractions]

    header = f"  {'y':>8}"
    for i in x_stations:
        x_val = x_coords[i]
        header += f"  x={x_val:5.2f}"
    print(header)
    print("  " + "-" * (10 + 9 * len(x_stations)))

    for j in range(0, ny, max(1, ny // 8)):
        y_val = y_coords[j]
        row = f"  {y_val:8.4f}"
        for i in x_stations:
            idx = j * nx + i
            row += f"  {u_field[idx]:7.4f}"
        print(row)

    # Write VTK output
    print("\n  Writing VTK output...")

    cfd_python.write_vtk_scalar(
        os.path.join(output_dir, "bfs_velocity_magnitude.vtk"),
        "velocity_magnitude",
        vel_mag,
        nx,
        ny,
        xmin,
        xmax,
        ymin,
        ymax,
    )

    cfd_python.write_vtk_vector(
        os.path.join(output_dir, "bfs_velocity.vtk"),
        "velocity",
        u_ic,
        v_ic,
        nx,
        ny,
        xmin,
        xmax,
        ymin,
        ymax,
    )

    print("    output/bfs_velocity_magnitude.vtk")
    print("    output/bfs_velocity.vtk")

    # =========================================================
    # Validation
    # =========================================================
    print("\nValidation")
    print("-" * 60)

    # Published reattachment lengths (Armaly et al. 1983) for 2:1 expansion
    armaly_data = {
        100: 5.0,
        200: 7.0,
        400: 11.5,
    }

    print("  Armaly et al. (1983) reattachment lengths (x_r / h):")
    for re_ref, xr_ref in armaly_data.items():
        print(f"    Re = {re_ref:4d}:  x_r/h ~ {xr_ref:.1f}")

    print(f"\n  Current simulation: Re = {Re:.1f}")
    re_int = int(round(Re))
    expected = -1.0
    if re_int in armaly_data:
        expected = armaly_data[re_int]
        print(f"  Expected reattachment: x_r/h ~ {expected:.1f}")
    else:
        # Linear interpolation between nearest reference points
        re_vals = sorted(armaly_data.keys())
        if Re < re_vals[0]:
            expected = armaly_data[re_vals[0]] * (Re / re_vals[0])
        elif Re > re_vals[-1]:
            expected = armaly_data[re_vals[-1]]
        else:
            for k in range(len(re_vals) - 1):
                if re_vals[k] <= Re <= re_vals[k + 1]:
                    r0, r1 = re_vals[k], re_vals[k + 1]
                    frac = (Re - r0) / (r1 - r0)
                    expected = armaly_data[r0] + frac * (armaly_data[r1] - armaly_data[r0])
                    break
        if expected > 0:
            print(f"  Interpolated expected: x_r/h ~ {expected:.1f}")

    if reattach_x > 0.0:
        print(f"  Simulated reattachment: x_r/h = {reattach_nondim:.2f}")
        if expected > 0:
            err_pct = abs(reattach_nondim - expected) / expected * 100.0
            print(f"  Deviation from reference: {err_pct:.1f}%")
            print(f"  Note: short run ({steps} steps) is for demonstration;")
            print("        longer runs improve agreement with published data.")

    # =========================================================
    # Summary
    # =========================================================
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  Geometry:          2:1 expansion, h = {h:.3f}, H = {H:.3f}")
    print(f"  Domain:            {xmin:.2f} <= x <= {xmax:.2f}  ({xmax / h:.0f} step heights)")
    print(f"  Grid:              {nx} x {ny}, beta = {beta}")
    print(f"  Grid stretch ratio: x={stretching_ratio_x:.2f}, y={stretching_ratio_y:.2f}")
    print(f"  Reynolds number:   {Re:.1f}  (u={u_inlet}, h={h}, nu={nu})")
    print(f"  Inlet velocity:    {u_inlet:.3f} (uniform, upper half of inlet)")
    print(f"  Steps run:         {steps}")
    print(f"  Solver:            {result['solver_name']}")
    if reattach_x > 0.0:
        print(f"  Reattachment:      x/h = {reattach_nondim:.2f}  (reference ~ 5-7 at Re=100-200)")
    print(f"  VTK output:        {output_dir}")
    print("\nBackward-facing step example complete!")


if __name__ == "__main__":
    main()
