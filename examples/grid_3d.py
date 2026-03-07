#!/usr/bin/env python3
"""
3D Grid Example (v0.2.0)

Demonstrates 3D grid creation and VTK output introduced in v0.2.0.
The create_grid() function now accepts optional nz, zmin, zmax parameters
to create 3D computational domains. VTK output functions similarly support
3D fields with the nz/zmin/zmax and w_data parameters.

3D grids are used for:
- Full 3D flow simulations (channel, pipe, cavity)
- Turbulence modeling (DNS, LES)
- Complex geometry with spanwise variation

New in v0.2.0:
- create_grid(nz=, zmin=, zmax=) for 3D grids
- write_vtk_scalar() with nz/zmin/zmax
- write_vtk_vector() with w_data/nz/zmin/zmax
- BC_EDGE_FRONT, BC_EDGE_BACK for z-direction boundaries
"""

import math
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


def main():
    print("CFD Python 3D Grid Example (v0.2.0)")
    print("=" * 60)

    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    # =================================================================
    # 1. 2D Grid (default behavior)
    # =================================================================
    print("\n1. 2D Grid (default, nz=1)")
    print("-" * 60)

    grid_2d = cfd_python.create_grid(
        nx=20,
        ny=20,
        xmin=0.0,
        xmax=1.0,
        ymin=0.0,
        ymax=1.0,
    )

    print(f"   Dimensions: {grid_2d['nx']} x {grid_2d['ny']}")
    print(f"   nz:         {grid_2d.get('nz', 1)}")
    print(f"   X range:    [{grid_2d['xmin']}, {grid_2d['xmax']}]")
    print(f"   Y range:    [{grid_2d['ymin']}, {grid_2d['ymax']}]")
    print(f"   X coords:   {len(grid_2d['x_coords'])} points")
    print(f"   Y coords:   {len(grid_2d['y_coords'])} points")

    # =================================================================
    # 2. 3D Grid
    # =================================================================
    print("\n2. 3D Grid")
    print("-" * 60)

    nx, ny, nz = 16, 16, 8
    grid_3d = cfd_python.create_grid(
        nx=nx,
        ny=ny,
        xmin=0.0,
        xmax=2.0,
        ymin=0.0,
        ymax=1.0,
        nz=nz,
        zmin=0.0,
        zmax=0.5,
    )

    print(f"   Dimensions: {grid_3d['nx']} x {grid_3d['ny']} x {grid_3d.get('nz', 1)}")
    print(f"   X range:    [{grid_3d['xmin']}, {grid_3d['xmax']}]")
    print(f"   Y range:    [{grid_3d['ymin']}, {grid_3d['ymax']}]")
    print(f"   Z range:    [{grid_3d.get('zmin', 0)}, {grid_3d.get('zmax', 0)}]")
    print(f"   X coords:   {len(grid_3d['x_coords'])} points")
    print(f"   Y coords:   {len(grid_3d['y_coords'])} points")
    if "z_coords" in grid_3d:
        print(f"   Z coords:   {len(grid_3d['z_coords'])} points")

    total_points = nx * ny * nz
    print(f"   Total cells: {total_points}")

    # =================================================================
    # 3. 3D Boundary Edge Constants
    # =================================================================
    print("\n3. 3D Boundary Edge Constants")
    print("-" * 60)

    edges = [
        ("BC_EDGE_LEFT", cfd_python.BC_EDGE_LEFT, "x = xmin"),
        ("BC_EDGE_RIGHT", cfd_python.BC_EDGE_RIGHT, "x = xmax"),
        ("BC_EDGE_BOTTOM", cfd_python.BC_EDGE_BOTTOM, "y = ymin"),
        ("BC_EDGE_TOP", cfd_python.BC_EDGE_TOP, "y = ymax"),
        ("BC_EDGE_FRONT", cfd_python.BC_EDGE_FRONT, "z = zmin (v0.2.0)"),
        ("BC_EDGE_BACK", cfd_python.BC_EDGE_BACK, "z = zmax (v0.2.0)"),
    ]

    for name, value, face in edges:
        print(f"   {name:20s} = {value}  ({face})")

    # =================================================================
    # 4. 3D Scalar Field VTK Output
    # =================================================================
    print("\n4. 3D Scalar Field VTK Output")
    print("-" * 60)

    # Generate a synthetic 3D scalar field (distance from center)
    dx = (grid_3d["xmax"] - grid_3d["xmin"]) / nx
    dy = (grid_3d["ymax"] - grid_3d["ymin"]) / ny
    dz = (grid_3d.get("zmax", 0) - grid_3d.get("zmin", 0)) / nz
    cx, cy, cz = 1.0, 0.5, 0.25  # domain center

    scalar_field = []
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                x = grid_3d["xmin"] + (i + 0.5) * dx
                y = grid_3d["ymin"] + (j + 0.5) * dy
                z = grid_3d.get("zmin", 0) + (k + 0.5) * dz
                r = math.sqrt((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2)
                scalar_field.append(r)

    vtk_file = os.path.join(output_dir, "scalar_3d.vtk")
    cfd_python.write_vtk_scalar(
        filename=vtk_file,
        field_name="distance",
        data=scalar_field,
        nx=nx,
        ny=ny,
        xmin=0.0,
        xmax=2.0,
        ymin=0.0,
        ymax=1.0,
        nz=nz,
        zmin=0.0,
        zmax=0.5,
    )
    print(f"   Wrote: output/scalar_3d.vtk ({len(scalar_field)} points)")

    # =================================================================
    # 5. 3D Vector Field VTK Output
    # =================================================================
    print("\n5. 3D Vector Field VTK Output")
    print("-" * 60)

    # Generate a synthetic 3D velocity field (solid body rotation around z-axis)
    u_data = []
    v_data = []
    w_data = []

    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                x = grid_3d["xmin"] + (i + 0.5) * dx - cx
                y = grid_3d["ymin"] + (j + 0.5) * dy - cy
                # Solid body rotation: u = -omega*y, v = omega*x
                omega = 1.0
                u_data.append(-omega * y)
                v_data.append(omega * x)
                w_data.append(0.0)  # no z-velocity

    vtk_file = os.path.join(output_dir, "vector_3d.vtk")
    cfd_python.write_vtk_vector(
        filename=vtk_file,
        field_name="velocity",
        u_data=u_data,
        v_data=v_data,
        nx=nx,
        ny=ny,
        xmin=0.0,
        xmax=2.0,
        ymin=0.0,
        ymax=1.0,
        w_data=w_data,
        nz=nz,
        zmin=0.0,
        zmax=0.5,
    )
    print(f"   Wrote: output/vector_3d.vtk ({len(u_data)} points)")

    # =================================================================
    # 6. Comparing 2D and 3D Grids
    # =================================================================
    print("\n6. Comparing 2D and 3D Grids")
    print("-" * 60)

    grids = [
        ("2D (50x50)", 50, 50, 1),
        ("3D (50x50x10)", 50, 50, 10),
        ("3D (50x50x50)", 50, 50, 50),
        ("3D (100x100x100)", 100, 100, 100),
    ]

    print(f"   {'Configuration':25s} {'Cells':>12s} {'Memory (f64)':>14s}")
    for label, gx, gy, gz in grids:
        cells = gx * gy * gz
        mem_mb = cells * 8 / (1024 * 1024)  # 8 bytes per double
        print(f"   {label:25s} {cells:>12,d} {mem_mb:>11.1f} MB")

    print("\n   Note: 3D simulations scale as O(n^3) — use coarser grids")
    print("   or GPU backends for large 3D problems.")

    # =================================================================
    # Summary
    # =================================================================
    print("\n" + "=" * 60)
    print("Summary")
    print("-" * 60)
    print("   New v0.2.0 3D capabilities:")
    print("     - create_grid(nz=, zmin=, zmax=)")
    print("     - write_vtk_scalar() with nz/zmin/zmax")
    print("     - write_vtk_vector() with w_data/nz/zmin/zmax")
    print("     - BC_EDGE_FRONT, BC_EDGE_BACK for z boundaries")
    print(f"\n   Output files in: {output_dir}")
    print("   Open .vtk files with ParaView for 3D visualization")


if __name__ == "__main__":
    main()
