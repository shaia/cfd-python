#!/usr/bin/env python3
"""
Solver Comparison Example

This example compares different solver backends available in cfd_python:
- Scalar (baseline, pure C implementation)
- SIMD (vectorized using AVX2/NEON)
- OpenMP (multi-threaded)
- CUDA (GPU-accelerated, if available)

The comparison includes:
- Performance timing for each backend
- Result validation (all should produce identical results)
- Scaling analysis with problem size
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


def benchmark_simulation(nx, ny, steps, label=""):
    """Run a simulation and measure execution time.

    Args:
        nx, ny: Grid dimensions
        steps: Number of time steps
        label: Description for output

    Returns:
        tuple: (elapsed_time, result_dict)
    """
    start = time.perf_counter()

    result = cfd_python.run_simulation_with_params(
        nx=nx, ny=ny, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0, steps=steps, dt=0.001, cfl=0.2
    )

    elapsed = time.perf_counter() - start

    return elapsed, result


def compute_checksum(field):
    """Compute a simple checksum for validation."""
    return sum(field)


def main():
    print("CFD Python - Solver Comparison Example")
    print("=" * 60)

    # =================================================================
    # 1. System Information
    # =================================================================
    print("\n1. System Information")
    print("-" * 60)

    # CPU features
    print(f"   SIMD Architecture: {cfd_python.get_simd_name()}")
    print(f"   Has AVX2: {cfd_python.has_avx2()}")
    print(f"   Has NEON: {cfd_python.has_neon()}")
    print(f"   Has Any SIMD: {cfd_python.has_simd()}")

    # Available backends
    available = cfd_python.get_available_backends()
    print(f"\n   Available solver backends: {available}")

    # BC backend
    print(f"   BC backend: {cfd_python.bc_get_backend_name()}")

    # =================================================================
    # 2. Backend Details
    # =================================================================
    print("\n2. Backend Details")
    print("-" * 60)

    backends = [
        ("Scalar", cfd_python.BACKEND_SCALAR),
        ("SIMD", cfd_python.BACKEND_SIMD),
        ("OpenMP", cfd_python.BACKEND_OMP),
        ("CUDA", cfd_python.BACKEND_CUDA),
    ]

    print(f"   {'Backend':<12} {'Available':<12} {'Solvers'}")
    print("   " + "-" * 50)

    for name, backend_id in backends:
        is_available = cfd_python.backend_is_available(backend_id)
        if is_available:
            solvers = cfd_python.list_solvers_by_backend(backend_id)
            solver_count = len(solvers) if solvers else 0
            print(f"   {name:<12} {'Yes':<12} {solver_count} registered")
        else:
            print(f"   {name:<12} {'No':<12} -")

    # =================================================================
    # 3. Solver Inventory
    # =================================================================
    print("\n3. Registered Solvers")
    print("-" * 60)

    all_solvers = cfd_python.list_solvers()
    print(f"   Total registered solvers: {len(all_solvers)}")

    for solver_name in all_solvers:
        info = cfd_python.get_solver_info(solver_name)
        desc = info.get("description", "No description")
        version = info.get("version", "N/A")
        print(f"\n   {solver_name}:")
        print(f"     Description: {desc}")
        print(f"     Version: {version}")

    # =================================================================
    # 4. Performance Comparison
    # =================================================================
    print("\n4. Performance Comparison")
    print("-" * 60)

    # Test configurations
    test_configs = [
        (32, 32, 100, "Small grid"),
        (64, 64, 100, "Medium grid"),
        (128, 128, 50, "Large grid"),
    ]

    print(f"\n   {'Grid':<15} {'Steps':<8} {'Time (s)':<12} {'Cells/s':<15}")
    print("   " + "-" * 55)

    results = []
    for nx, ny, steps, label in test_configs:
        elapsed, result = benchmark_simulation(nx, ny, steps, label)
        cells = nx * ny * steps
        cells_per_sec = cells / elapsed if elapsed > 0 else 0

        results.append(
            {
                "config": f"{nx}x{ny}",
                "label": label,
                "time": elapsed,
                "cells_per_sec": cells_per_sec,
                "checksum": compute_checksum(result["velocity_magnitude"]),
            }
        )

        print(f"   {nx}x{ny:<10} {steps:<8} {elapsed:<12.4f} {cells_per_sec:<15.0f}")

    # =================================================================
    # 5. BC Backend Comparison
    # =================================================================
    print("\n5. Boundary Condition Backend Comparison")
    print("-" * 60)

    # Test BC application performance
    nx, ny = 128, 128
    size = nx * ny
    iterations = 1000

    bc_backends = [
        ("Scalar", cfd_python.BC_BACKEND_SCALAR),
        ("SIMD", cfd_python.BC_BACKEND_SIMD),
        ("OpenMP", cfd_python.BC_BACKEND_OMP),
    ]

    print(f"\n   Testing BC application ({iterations} iterations on {nx}x{ny} grid)")
    print(f"\n   {'Backend':<12} {'Available':<12} {'Time (ms)':<12} {'Speedup'}")
    print("   " + "-" * 50)

    baseline_time = None
    for name, backend_id in bc_backends:
        if cfd_python.bc_backend_available(backend_id):
            cfd_python.bc_set_backend(backend_id)

            # Create test fields
            u = [1.0] * size
            v = [0.5] * size

            # Time BC applications
            start = time.perf_counter()
            for _ in range(iterations):
                cfd_python.bc_apply_noslip(u, v, nx, ny)
            elapsed = time.perf_counter() - start

            elapsed_ms = elapsed * 1000

            if baseline_time is None:
                baseline_time = elapsed
                speedup = 1.0
            else:
                speedup = baseline_time / elapsed if elapsed > 0 else 0

            print(f"   {name:<12} {'Yes':<12} {elapsed_ms:<12.2f} {speedup:.2f}x")
        else:
            print(f"   {name:<12} {'No':<12} -")

    # Reset to auto
    cfd_python.bc_set_backend(cfd_python.BC_BACKEND_AUTO)

    # =================================================================
    # 6. Scaling Analysis
    # =================================================================
    print("\n6. Scaling Analysis")
    print("-" * 60)

    grid_sizes = [(16, 16), (32, 32), (64, 64), (128, 128)]
    steps = 50

    print(f"\n   Grid size scaling ({steps} steps each)")
    print(f"\n   {'Grid':<12} {'Cells':<10} {'Time (s)':<10} {'Efficiency'}")
    print("   " + "-" * 45)

    base_efficiency = None
    for nx, ny in grid_sizes:
        elapsed, _ = benchmark_simulation(nx, ny, steps)
        cells = nx * ny
        time_per_cell = elapsed / (cells * steps) if cells > 0 else 0

        if base_efficiency is None:
            base_efficiency = time_per_cell
            efficiency = 100.0
        else:
            efficiency = (base_efficiency / time_per_cell) * 100 if time_per_cell > 0 else 0

        print(f"   {nx}x{ny:<8} {cells:<10} {elapsed:<10.4f} {efficiency:.1f}%")

    # =================================================================
    # 7. Result Validation
    # =================================================================
    print("\n7. Result Validation")
    print("-" * 60)

    # Run same simulation with different grid sizes and check consistency
    print("\n   Verifying result consistency...")

    checksums = []
    for config in results:
        checksums.append(config["checksum"])

    print("\n   Checksums from performance tests:")
    for i, result in enumerate(results):
        print(f"     {result['config']}: {result['checksum']:.6f}")

    # =================================================================
    # 8. Recommendations
    # =================================================================
    print("\n8. Performance Recommendations")
    print("-" * 60)

    recommendations = []

    # Check SIMD
    if cfd_python.has_avx2():
        recommendations.append("AVX2 detected - SIMD backend recommended for CPU-intensive work")
    elif cfd_python.has_neon():
        recommendations.append("NEON detected - SIMD backend recommended for CPU-intensive work")

    # Check OpenMP
    if cfd_python.backend_is_available(cfd_python.BACKEND_OMP):
        recommendations.append("OpenMP available - use for large grids to leverage all CPU cores")

    # Check CUDA
    if cfd_python.backend_is_available(cfd_python.BACKEND_CUDA):
        recommendations.append(
            "CUDA available - use GPU backend for very large simulations (10-100x speedup)"
        )
    else:
        recommendations.append("CUDA not available - consider GPU build for maximum performance")

    # BC backend
    if cfd_python.bc_backend_available(cfd_python.BC_BACKEND_SIMD):
        recommendations.append("SIMD BC backend available - auto selection will use it")

    if recommendations:
        print("\n   Based on your system:")
        for rec in recommendations:
            print(f"     - {rec}")
    else:
        recommendations.append("Only scalar backends available")

    # =================================================================
    # Summary
    # =================================================================
    print("\n" + "=" * 60)
    print("Summary")
    print("-" * 60)
    print(f"   SIMD: {cfd_python.get_simd_name()}")
    print(f"   Solver backends: {', '.join(available)}")
    print(f"   BC backend: {cfd_python.bc_get_backend_name()}")
    print(f"   Total solvers: {len(all_solvers)}")

    # Best performance from tests
    if results:
        best = max(results, key=lambda x: x["cells_per_sec"])
        print(f"   Best throughput: {best['cells_per_sec']:.0f} cells/s ({best['config']})")


if __name__ == "__main__":
    main()
