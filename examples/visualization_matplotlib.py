#!/usr/bin/env python3
"""
Matplotlib Visualization Example

This example demonstrates how to visualize CFD simulation results using
matplotlib. It creates various plots including contour plots, streamlines,
vector fields, and convergence history.

Requirements:
    pip install matplotlib numpy
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import matplotlib.pyplot as plt
    import numpy as np

    import cfd_python
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure to install dependencies:")
    print("  pip install matplotlib numpy")
    print("  pip install -e .")
    sys.exit(1)


def create_vortex_field(nx, ny, xmin, xmax, ymin, ymax):
    """Create a synthetic vortex velocity field for visualization."""
    dx = (xmax - xmin) / (nx - 1)
    dy = (ymax - ymin) / (ny - 1)
    xc, yc = (xmax + xmin) / 2, (ymax + ymin) / 2

    u = [0.0] * (nx * ny)
    v = [0.0] * (nx * ny)
    p = [0.0] * (nx * ny)

    for j in range(ny):
        y = ymin + j * dy
        for i in range(nx):
            x = xmin + i * dx
            idx = j * nx + i

            rx, ry = x - xc, y - yc
            r = np.sqrt(rx * rx + ry * ry) + 1e-10

            # Rankine vortex
            core_radius = 0.3
            strength = 1.0
            if r < core_radius:
                factor = r / core_radius
            else:
                factor = core_radius / r

            u[idx] = -ry / r * strength * factor
            v[idx] = rx / r * strength * factor
            p[idx] = 1.0 - 0.5 * (strength * factor) ** 2

    return u, v, p


def main():
    print("CFD Python - Matplotlib Visualization Example")
    print("=" * 60)

    # =================================================================
    # 1. Run Simulation
    # =================================================================
    print("\n1. Running Simulation")
    print("-" * 60)

    nx, ny = 64, 64
    xmin, xmax = 0.0, 1.0
    ymin, ymax = 0.0, 1.0

    result = cfd_python.run_simulation_with_params(
        nx=nx,
        ny=ny,
        xmin=xmin,
        xmax=xmax,
        ymin=ymin,
        ymax=ymax,
        steps=100,
        dt=0.001,
        cfl=0.2,
    )

    print(f"   Grid: {nx} x {ny}")
    print(f"   Solver: {result['solver_name']}")

    # Get velocity magnitude from simulation
    vel_mag_sim = np.array(result["velocity_magnitude"]).reshape(ny, nx)

    # Create coordinate arrays
    x = np.linspace(xmin, xmax, nx)
    y = np.linspace(ymin, ymax, ny)
    X, Y = np.meshgrid(x, y)

    # =================================================================
    # 2. Velocity Magnitude Contour Plot
    # =================================================================
    print("\n2. Creating Velocity Magnitude Contour Plot")
    print("-" * 60)

    fig, ax = plt.subplots(figsize=(8, 6))
    contour = ax.contourf(X, Y, vel_mag_sim, levels=20, cmap="viridis")
    plt.colorbar(contour, ax=ax, label="Velocity Magnitude")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("Velocity Magnitude Field")
    ax.set_aspect("equal")
    plt.savefig("velocity_magnitude_contour.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("   Saved: velocity_magnitude_contour.png")

    # =================================================================
    # 3. Synthetic Vortex Visualization
    # =================================================================
    print("\n3. Creating Vortex Flow Visualization")
    print("-" * 60)

    # Create vortex field for richer visualization
    u, v, p = create_vortex_field(nx, ny, xmin, xmax, ymin, ymax)
    U = np.array(u).reshape(ny, nx)
    V = np.array(v).reshape(ny, nx)
    P = np.array(p).reshape(ny, nx)
    vel_mag = np.sqrt(U**2 + V**2)

    # Create multi-panel figure
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Panel 1: Velocity magnitude with contours
    ax1 = axes[0, 0]
    cf1 = ax1.contourf(X, Y, vel_mag, levels=20, cmap="plasma")
    ax1.contour(X, Y, vel_mag, levels=10, colors="white", linewidths=0.5, alpha=0.5)
    plt.colorbar(cf1, ax=ax1, label="Velocity Magnitude")
    ax1.set_xlabel("X")
    ax1.set_ylabel("Y")
    ax1.set_title("Velocity Magnitude")
    ax1.set_aspect("equal")

    # Panel 2: Pressure field
    ax2 = axes[0, 1]
    cf2 = ax2.contourf(X, Y, P, levels=20, cmap="coolwarm")
    plt.colorbar(cf2, ax=ax2, label="Pressure")
    ax2.set_xlabel("X")
    ax2.set_ylabel("Y")
    ax2.set_title("Pressure Field")
    ax2.set_aspect("equal")

    # Panel 3: Vector field (quiver plot)
    ax3 = axes[1, 0]
    skip = 4  # Skip every N points for clarity
    ax3.quiver(
        X[::skip, ::skip],
        Y[::skip, ::skip],
        U[::skip, ::skip],
        V[::skip, ::skip],
        vel_mag[::skip, ::skip],
        cmap="viridis",
        scale=15,
    )
    ax3.set_xlabel("X")
    ax3.set_ylabel("Y")
    ax3.set_title("Velocity Vectors")
    ax3.set_aspect("equal")

    # Panel 4: Streamlines
    ax4 = axes[1, 1]
    strm = ax4.streamplot(X, Y, U, V, color=vel_mag, cmap="viridis", density=2, linewidth=1)
    plt.colorbar(strm.lines, ax=ax4, label="Velocity Magnitude")
    ax4.set_xlabel("X")
    ax4.set_ylabel("Y")
    ax4.set_title("Streamlines")
    ax4.set_aspect("equal")

    plt.tight_layout()
    plt.savefig("vortex_visualization.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("   Saved: vortex_visualization.png")

    # =================================================================
    # 4. Centerline Profiles
    # =================================================================
    print("\n4. Creating Centerline Profile Plots")
    print("-" * 60)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Horizontal centerline (y = 0.5)
    j_center = ny // 2
    ax1 = axes[0]
    ax1.plot(x, vel_mag[j_center, :], "b-", linewidth=2, label="Velocity Magnitude")
    ax1.plot(x, U[j_center, :], "r--", linewidth=1.5, label="U velocity")
    ax1.plot(x, V[j_center, :], "g--", linewidth=1.5, label="V velocity")
    ax1.set_xlabel("X")
    ax1.set_ylabel("Velocity")
    ax1.set_title(f"Horizontal Centerline (y = {y[j_center]:.2f})")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Vertical centerline (x = 0.5)
    i_center = nx // 2
    ax2 = axes[1]
    ax2.plot(y, vel_mag[:, i_center], "b-", linewidth=2, label="Velocity Magnitude")
    ax2.plot(y, U[:, i_center], "r--", linewidth=1.5, label="U velocity")
    ax2.plot(y, V[:, i_center], "g--", linewidth=1.5, label="V velocity")
    ax2.set_xlabel("Y")
    ax2.set_ylabel("Velocity")
    ax2.set_title(f"Vertical Centerline (x = {x[i_center]:.2f})")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("centerline_profiles.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("   Saved: centerline_profiles.png")

    # =================================================================
    # 5. Convergence History
    # =================================================================
    print("\n5. Creating Convergence History Plot")
    print("-" * 60)

    # Run multiple steps and track convergence
    max_velocities = []
    residuals = []
    steps_list = []
    prev_vel = None

    for step in range(50):
        result = cfd_python.run_simulation_with_params(
            nx=32, ny=32, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0, steps=1, dt=0.001
        )
        vel = np.array(result["velocity_magnitude"])
        stats = cfd_python.calculate_field_stats(result["velocity_magnitude"])
        max_velocities.append(stats["max"])
        steps_list.append(step)

        if prev_vel is not None:
            residual = np.mean(np.abs(vel - prev_vel))
            residuals.append(residual)
        else:
            residuals.append(np.nan)
        prev_vel = vel.copy()

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Max velocity history
    ax1 = axes[0]
    ax1.plot(steps_list, max_velocities, "b-", linewidth=2)
    ax1.set_xlabel("Step")
    ax1.set_ylabel("Max Velocity")
    ax1.set_title("Maximum Velocity History")
    ax1.grid(True, alpha=0.3)

    # Residual history (skip first NaN, filter zeros for log scale)
    ax2 = axes[1]
    valid_residuals = [r if r > 0 else 1e-16 for r in residuals[1:]]
    ax2.semilogy(steps_list[1:], valid_residuals, "r-", linewidth=2)
    ax2.set_xlabel("Step")
    ax2.set_ylabel("Residual (L1 norm)")
    ax2.set_title("Convergence History")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("convergence_history.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("   Saved: convergence_history.png")

    # =================================================================
    # 6. Grid Comparison
    # =================================================================
    print("\n6. Creating Grid Resolution Comparison")
    print("-" * 60)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    grid_sizes = [(16, 16), (32, 32), (64, 64)]

    for idx, (gx, gy) in enumerate(grid_sizes):
        result = cfd_python.run_simulation_with_params(
            nx=gx, ny=gy, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0, steps=50, dt=0.001
        )
        vel = np.array(result["velocity_magnitude"]).reshape(gy, gx)
        xx = np.linspace(0, 1, gx)
        yy = np.linspace(0, 1, gy)
        XX, YY = np.meshgrid(xx, yy)

        ax = axes[idx]
        cf = ax.contourf(XX, YY, vel, levels=15, cmap="viridis")
        plt.colorbar(cf, ax=ax, label="Velocity")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_title(f"Grid: {gx}x{gy}")
        ax.set_aspect("equal")

    plt.tight_layout()
    plt.savefig("grid_comparison.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("   Saved: grid_comparison.png")

    # =================================================================
    # 7. 3D Surface Plot
    # =================================================================
    print("\n7. Creating 3D Surface Plot")
    print("-" * 60)

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")

    # Use the vortex velocity magnitude
    surf = ax.plot_surface(X, Y, vel_mag, cmap="viridis", edgecolor="none", alpha=0.8)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Velocity Magnitude")
    ax.set_title("3D Velocity Magnitude Surface")
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label="Velocity")
    plt.savefig("velocity_surface_3d.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("   Saved: velocity_surface_3d.png")

    # =================================================================
    # Summary
    # =================================================================
    print("\n" + "=" * 60)
    print("Visualization Example Complete!")
    print("=" * 60)
    print("\nGenerated files:")
    print("  - velocity_magnitude_contour.png: Basic contour plot")
    print("  - vortex_visualization.png: Multi-panel vortex analysis")
    print("  - centerline_profiles.png: 1D profile plots")
    print("  - convergence_history.png: Convergence monitoring")
    print("  - grid_comparison.png: Grid resolution study")
    print("  - velocity_surface_3d.png: 3D surface visualization")
    print("\nVisualization tips:")
    print("  - Use contourf for filled contours, contour for lines")
    print("  - Use quiver for vector fields (skip points for clarity)")
    print("  - Use streamplot for streamlines")
    print("  - Use semilogy for convergence plots")


if __name__ == "__main__":
    main()
