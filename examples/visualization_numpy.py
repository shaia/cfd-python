#!/usr/bin/env python3
"""
NumPy Visualization Example

Demonstrates how to use NumPy with CFD Python results for
analysis and visualization preparation.

Note: This example uses only NumPy. For actual plotting,
you would use matplotlib (see visualization_matplotlib.py).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np

import cfd_python


def main():
    print("CFD Python - NumPy Analysis Example")
    print("=" * 50)

    # Run simulation
    nx, ny = 30, 30
    print(f"\n1. Running simulation ({nx}x{ny} grid, 50 steps)...")
    print("-" * 50)

    result = cfd_python.run_simulation(
        nx=nx, ny=ny, steps=50, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0
    )

    # Convert to NumPy array and reshape to 2D grid
    vel_mag = np.array(result).reshape((ny, nx))
    print(f"   Result shape: {vel_mag.shape}")

    # Basic statistics
    print("\n2. Statistical Analysis")
    print("-" * 50)

    print(f"   Min velocity:    {np.min(vel_mag):.6f}")
    print(f"   Max velocity:    {np.max(vel_mag):.6f}")
    print(f"   Mean velocity:   {np.mean(vel_mag):.6f}")
    print(f"   Std deviation:   {np.std(vel_mag):.6f}")
    print(f"   Median:          {np.median(vel_mag):.6f}")

    # Percentiles
    print("\n3. Percentile Analysis")
    print("-" * 50)

    percentiles = [10, 25, 50, 75, 90, 99]
    for p in percentiles:
        val = np.percentile(vel_mag, p)
        print(f"   {p:2d}th percentile: {val:.6f}")

    # Spatial analysis
    print("\n4. Spatial Analysis")
    print("-" * 50)

    # Extract centerlines
    mid_y = ny // 2
    mid_x = nx // 2

    horizontal_centerline = vel_mag[mid_y, :]
    vertical_centerline = vel_mag[:, mid_x]

    print(f"   Horizontal centerline (y={mid_y}):")
    print(f"     Min: {np.min(horizontal_centerline):.6f}")
    print(f"     Max: {np.max(horizontal_centerline):.6f}")

    print(f"   Vertical centerline (x={mid_x}):")
    print(f"     Min: {np.min(vertical_centerline):.6f}")
    print(f"     Max: {np.max(vertical_centerline):.6f}")

    # Find location of maximum velocity
    max_idx = np.unravel_index(np.argmax(vel_mag), vel_mag.shape)
    print(f"\n   Maximum velocity location: ({max_idx[1]}, {max_idx[0]})")

    # Grid analysis - divide into quadrants
    print("\n5. Quadrant Analysis")
    print("-" * 50)

    q1 = vel_mag[: ny // 2, : nx // 2]  # Bottom-left
    q2 = vel_mag[: ny // 2, nx // 2 :]  # Bottom-right
    q3 = vel_mag[ny // 2 :, : nx // 2]  # Top-left
    q4 = vel_mag[ny // 2 :, nx // 2 :]  # Top-right

    quadrants = [("Bottom-left", q1), ("Bottom-right", q2), ("Top-left", q3), ("Top-right", q4)]

    for name, q in quadrants:
        print(f"   {name:12s}: mean={np.mean(q):.6f}, max={np.max(q):.6f}")

    # Gradient analysis
    print("\n6. Gradient Analysis")
    print("-" * 50)

    # Compute gradients
    grad_y, grad_x = np.gradient(vel_mag)
    grad_magnitude = np.sqrt(grad_x**2 + grad_y**2)

    print(f"   Max gradient magnitude: {np.max(grad_magnitude):.6f}")
    print(f"   Mean gradient magnitude: {np.mean(grad_magnitude):.6f}")

    # Find steepest gradient location
    steep_idx = np.unravel_index(np.argmax(grad_magnitude), grad_magnitude.shape)
    print(f"   Steepest gradient at: ({steep_idx[1]}, {steep_idx[0]})")

    # Create coordinate arrays
    print("\n7. Coordinate Grid")
    print("-" * 50)

    grid_info = cfd_python.create_grid(nx, ny, 0.0, 1.0, 0.0, 1.0)
    x = np.array(grid_info["x_coords"])
    y = np.array(grid_info["y_coords"])
    X, Y = np.meshgrid(x, y)

    print(f"   X range: [{X.min():.3f}, {X.max():.3f}]")
    print(f"   Y range: [{Y.min():.3f}, {Y.max():.3f}]")

    # Export data for external plotting
    print("\n8. Data Export for Plotting")
    print("-" * 50)

    # Save as CSV for external tools
    output_file = "velocity_data.csv"
    flat_data = np.column_stack([X.flatten(), Y.flatten(), vel_mag.flatten()])
    np.savetxt(output_file, flat_data, delimiter=",", header="x,y,velocity_magnitude", comments="")
    print(f"   Saved to: {output_file}")
    print(f"   Shape: {flat_data.shape}")

    print("\n" + "=" * 50)
    print("NumPy analysis example completed!")
    print("\nTo visualize, use matplotlib:")
    print("  import matplotlib.pyplot as plt")
    print("  plt.contourf(X, Y, vel_mag)")
    print("  plt.colorbar()")
    print("  plt.show()")


if __name__ == "__main__":
    main()
