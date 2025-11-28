#!/usr/bin/env python3
"""
Output Formats Example

Demonstrates how to export simulation results to various formats:
- VTK files for visualization (ParaView, VisIt)
- CSV files for data analysis
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import cfd_python
import tempfile
from pathlib import Path


def main():
    print("CFD Python - Output Formats Example")
    print("=" * 50)

    # Create output directory
    output_dir = Path(tempfile.mkdtemp(prefix="cfd_output_"))
    print(f"\nOutput directory: {output_dir}\n")

    # Set the output directory for the library
    cfd_python.set_output_dir(str(output_dir))

    # Simulation parameters
    nx, ny = 20, 20
    xmin, xmax = 0.0, 1.0
    ymin, ymax = 0.0, 1.0

    # Run a simulation to get data
    print("1. Running Simulation")
    print("-" * 50)

    result = cfd_python.run_simulation(nx, ny, steps=10)
    print(f"   Simulation complete: {len(result)} points")

    # Create sample data for output examples
    size = nx * ny
    u_data = [0.1 * (i % nx) / nx for i in range(size)]  # Velocity X
    v_data = [0.05 * (i // nx) / ny for i in range(size)]  # Velocity Y
    p_data = [1.0 + 0.1 * i / size for i in range(size)]  # Pressure

    # VTK Scalar Output
    print("\n2. VTK Scalar Field Output")
    print("-" * 50)

    vtk_scalar_file = output_dir / "pressure_field.vtk"
    cfd_python.write_vtk_scalar(
        str(vtk_scalar_file),
        "pressure",
        p_data,
        nx, ny,
        xmin, xmax, ymin, ymax
    )
    print(f"   Written: {vtk_scalar_file.name}")
    print(f"   Size: {vtk_scalar_file.stat().st_size} bytes")

    # VTK with velocity magnitude
    vtk_velmag_file = output_dir / "velocity_magnitude.vtk"
    cfd_python.write_vtk_scalar(
        str(vtk_velmag_file),
        "velocity_magnitude",
        result,
        nx, ny,
        xmin, xmax, ymin, ymax
    )
    print(f"   Written: {vtk_velmag_file.name}")

    # VTK Vector Output
    print("\n3. VTK Vector Field Output")
    print("-" * 50)

    vtk_vector_file = output_dir / "velocity_field.vtk"
    cfd_python.write_vtk_vector(
        str(vtk_vector_file),
        "velocity",
        u_data, v_data,
        nx, ny,
        xmin, xmax, ymin, ymax
    )
    print(f"   Written: {vtk_vector_file.name}")
    print(f"   Size: {vtk_vector_file.stat().st_size} bytes")

    # CSV Timeseries Output
    print("\n4. CSV Timeseries Output")
    print("-" * 50)

    csv_file = output_dir / "simulation_timeseries.csv"

    # Write initial state (create new file)
    cfd_python.write_csv_timeseries(
        str(csv_file),
        step=0, time=0.0,
        u_data=u_data, v_data=v_data, p_data=p_data,
        nx=nx, ny=ny,
        dt=0.001, iterations=0,
        create_new=True
    )
    print(f"   Created: {csv_file.name}")

    # Append more timesteps
    for step in range(1, 6):
        time = step * 0.001
        cfd_python.write_csv_timeseries(
            str(csv_file),
            step=step, time=time,
            u_data=u_data, v_data=v_data, p_data=p_data,
            nx=nx, ny=ny,
            dt=0.001, iterations=step * 5,
            create_new=False
        )
    print(f"   Appended 5 timesteps")
    print(f"   Final size: {csv_file.stat().st_size} bytes")

    # Output Type Constants
    print("\n5. Output Type Constants")
    print("-" * 50)

    print("   Available output types:")
    print(f"   - OUTPUT_PRESSURE = {cfd_python.OUTPUT_PRESSURE}")
    print(f"   - OUTPUT_VELOCITY = {cfd_python.OUTPUT_VELOCITY}")
    print(f"   - OUTPUT_FULL_FIELD = {cfd_python.OUTPUT_FULL_FIELD}")
    print(f"   - OUTPUT_CSV_TIMESERIES = {cfd_python.OUTPUT_CSV_TIMESERIES}")
    print(f"   - OUTPUT_CSV_CENTERLINE = {cfd_python.OUTPUT_CSV_CENTERLINE}")
    print(f"   - OUTPUT_CSV_STATISTICS = {cfd_python.OUTPUT_CSV_STATISTICS}")

    # Summary
    print("\n6. Output Files Summary")
    print("-" * 50)

    print(f"\n   All files written to: {output_dir}\n")
    for f in sorted(output_dir.iterdir()):
        print(f"   - {f.name} ({f.stat().st_size} bytes)")

    print("\n" + "=" * 50)
    print("Output formats example completed!")
    print(f"\nVTK files can be opened with ParaView or VisIt.")
    print(f"CSV files can be opened with Excel, Python pandas, etc.")


if __name__ == "__main__":
    main()
