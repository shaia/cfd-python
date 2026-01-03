#!/usr/bin/env python3
"""
VTK Output Example

This example demonstrates the VTK output capabilities of cfd_python for
visualizing simulation results in ParaView or other VTK-compatible tools.

VTK (Visualization Toolkit) format is widely used for scientific visualization.
This example shows how to:
- Write scalar fields (pressure, temperature, velocity magnitude)
- Write vector fields (velocity, vorticity)
- Create time series output for animations
- Configure output directories
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


def create_sample_fields(nx, ny, xmin, xmax, ymin, ymax):
    """Create sample fields for visualization.

    Creates synthetic data representing typical CFD quantities:
    - Velocity field with a vortex pattern
    - Pressure field with gradients
    - Temperature field with boundary layer

    Args:
        nx, ny: Grid dimensions
        xmin, xmax, ymin, ymax: Domain bounds

    Returns:
        dict: Dictionary of field arrays
    """
    import math

    size = nx * ny
    dx = (xmax - xmin) / (nx - 1)
    dy = (ymax - ymin) / (ny - 1)

    # Initialize fields
    u = [0.0] * size  # x-velocity
    v = [0.0] * size  # y-velocity
    p = [0.0] * size  # pressure
    T = [0.0] * size  # temperature

    # Center of domain
    xc = (xmax + xmin) / 2
    yc = (ymax + ymin) / 2

    for j in range(ny):
        y = ymin + j * dy
        for i in range(nx):
            x = xmin + i * dx
            idx = j * nx + i

            # Create a vortex pattern for velocity
            rx = x - xc
            ry = y - yc
            r = math.sqrt(rx * rx + ry * ry) + 1e-10

            # Rankine vortex velocity profile
            vortex_strength = 1.0
            core_radius = 0.3
            if r < core_radius:
                factor = r / core_radius
            else:
                factor = core_radius / r

            u[idx] = -vortex_strength * factor * ry / r
            v[idx] = vortex_strength * factor * rx / r

            # Pressure decreases toward vortex center
            p[idx] = 1.0 - 0.5 * (vortex_strength * factor) ** 2

            # Temperature with thermal boundary layer
            # Hot on bottom, cold on top
            T[idx] = 100.0 * (1.0 - y / ymax)
            # Add some perturbation from velocity
            T[idx] += 10.0 * math.exp(-(r**2) / (2 * core_radius**2))

    return {"u": u, "v": v, "pressure": p, "temperature": T}


def main():
    print("CFD Python - VTK Output Example")
    print("=" * 60)

    # =================================================================
    # 1. Setup
    # =================================================================
    print("\n1. Setup")
    print("-" * 60)

    # Grid parameters
    nx, ny = 64, 64
    xmin, xmax = 0.0, 2.0
    ymin, ymax = 0.0, 2.0

    print(f"   Grid: {nx} x {ny}")
    print(f"   Domain: [{xmin}, {xmax}] x [{ymin}, {ymax}]")

    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    cfd_python.set_output_dir(output_dir)
    print("   Output directory: output/")

    # Create sample data
    fields = create_sample_fields(nx, ny, xmin, xmax, ymin, ymax)
    print("   Created sample vortex flow data")

    # =================================================================
    # 2. Writing Scalar Fields
    # =================================================================
    print("\n2. Writing Scalar Fields")
    print("-" * 60)

    # Write pressure field
    cfd_python.write_vtk_scalar(
        os.path.join(output_dir, "pressure.vtk"),
        "pressure",
        fields["pressure"],
        nx,
        ny,
        xmin,
        xmax,
        ymin,
        ymax,
    )
    print("   Written: output/pressure.vtk")

    # Write temperature field
    cfd_python.write_vtk_scalar(
        os.path.join(output_dir, "temperature.vtk"),
        "temperature",
        fields["temperature"],
        nx,
        ny,
        xmin,
        xmax,
        ymin,
        ymax,
    )
    print("   Written: output/temperature.vtk")

    # Compute and write velocity magnitude
    vel_mag = cfd_python.compute_velocity_magnitude(fields["u"], fields["v"], nx, ny)
    cfd_python.write_vtk_scalar(
        os.path.join(output_dir, "velocity_magnitude.vtk"),
        "velocity_magnitude",
        vel_mag,
        nx,
        ny,
        xmin,
        xmax,
        ymin,
        ymax,
    )
    print("   Written: output/velocity_magnitude.vtk")

    # =================================================================
    # 3. Writing Vector Fields
    # =================================================================
    print("\n3. Writing Vector Fields")
    print("-" * 60)

    # Write velocity vector field
    cfd_python.write_vtk_vector(
        os.path.join(output_dir, "velocity.vtk"),
        "velocity",
        fields["u"],
        fields["v"],
        nx,
        ny,
        xmin,
        xmax,
        ymin,
        ymax,
    )
    print("   Written: output/velocity.vtk")

    # =================================================================
    # 4. Time Series Output
    # =================================================================
    print("\n4. Time Series Output")
    print("-" * 60)
    print("   Creating animated vortex sequence...")

    import math

    # Create a series of snapshots showing vortex evolution
    n_frames = 10
    for frame in range(n_frames):
        # Rotate the vortex pattern
        angle = frame * 2 * math.pi / n_frames

        # Create rotated velocity field
        u_rot = [0.0] * (nx * ny)
        v_rot = [0.0] * (nx * ny)

        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        for idx in range(nx * ny):
            u_orig = fields["u"][idx]
            v_orig = fields["v"][idx]
            u_rot[idx] = u_orig * cos_a - v_orig * sin_a
            v_rot[idx] = u_orig * sin_a + v_orig * cos_a

        # Compute velocity magnitude for this frame
        vel_mag_frame = cfd_python.compute_velocity_magnitude(u_rot, v_rot, nx, ny)

        # Write with frame number in filename
        filename = os.path.join(output_dir, f"vortex_{frame:04d}.vtk")
        cfd_python.write_vtk_scalar(
            filename, "velocity_magnitude", vel_mag_frame, nx, ny, xmin, xmax, ymin, ymax
        )

    print(f"   Written: output/vortex_0000.vtk through output/vortex_{n_frames-1:04d}.vtk")
    print("   (Load in ParaView as a time series)")

    # =================================================================
    # 5. CSV Output for Analysis
    # =================================================================
    print("\n5. CSV Output for Analysis")
    print("-" * 60)

    # Write velocity magnitude as CSV using Python
    with open(os.path.join(output_dir, "velocity_magnitude.csv"), "w") as f:
        f.write("i,j,value\n")
        for j in range(ny):
            for i in range(nx):
                f.write(f"{i},{j},{vel_mag[j * nx + i]}\n")
    print("   Written: output/velocity_magnitude.csv")

    # Write pressure as CSV
    with open(os.path.join(output_dir, "pressure.csv"), "w") as f:
        f.write("i,j,value\n")
        for j in range(ny):
            for i in range(nx):
                f.write(f"{i},{j},{fields['pressure'][j * nx + i]}\n")
    print("   Written: output/pressure.csv")

    # =================================================================
    # 6. Field Statistics
    # =================================================================
    print("\n6. Field Statistics")
    print("-" * 60)

    # Compute statistics for each field
    for name, field in [
        ("velocity_magnitude", vel_mag),
        ("pressure", fields["pressure"]),
        ("temperature", fields["temperature"]),
    ]:
        stats = cfd_python.calculate_field_stats(field)
        print(f"\n   {name}:")
        print(f"     Min: {stats['min']:.4f}")
        print(f"     Max: {stats['max']:.4f}")
        print(f"     Avg: {stats['avg']:.4f}")

    # Flow statistics (includes all velocity components)
    print("\n   Flow statistics:")
    flow_stats = cfd_python.compute_flow_statistics(
        fields["u"], fields["v"], fields["pressure"], nx, ny
    )
    print(f"     Velocity magnitude max: {flow_stats['velocity_magnitude']['max']:.4f}")
    print(f"     Pressure max: {flow_stats['p']['max']:.4f}")

    # =================================================================
    # Summary
    # =================================================================
    print("\n" + "=" * 60)
    print("VTK Output Summary")
    print("-" * 60)
    print("   Output directory: output/")
    print("\n   Files created:")
    print("     Scalar fields:")
    print("       - output/pressure.vtk")
    print("       - output/temperature.vtk")
    print("       - output/velocity_magnitude.vtk")
    print("     Vector fields:")
    print("       - output/velocity.vtk")
    print("     Time series:")
    print(f"       - output/vortex_0000.vtk to output/vortex_{n_frames-1:04d}.vtk")
    print("     CSV files:")
    print("       - output/velocity_magnitude.csv")
    print("       - output/pressure.csv")
    print("\n   To visualize:")
    print("     1. Open ParaView")
    print("     2. File -> Open -> Select VTK file")
    print("     3. Click 'Apply' in Properties panel")
    print("     4. For vectors: Filters -> Glyph")
    print("     5. For time series: Use playback controls")


if __name__ == "__main__":
    main()
