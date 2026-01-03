#!/usr/bin/env python3
"""
Backend Detection Example

This example demonstrates how to query and use different compute backends
in cfd_python. It covers solver backends, BC backends, and CPU feature detection.
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


def main():
    print("CFD Python Backend Detection Example")
    print("=" * 60)
    print(f"Version: {cfd_python.__version__}")

    # =================================================================
    # 1. CPU Feature Detection
    # =================================================================
    print("\n1. CPU Feature Detection")
    print("-" * 60)

    # Get SIMD architecture
    arch = cfd_python.get_simd_arch()
    arch_name = cfd_python.get_simd_name()

    print(f"   SIMD Architecture: {arch_name} (id={arch})")

    # Check specific capabilities
    has_avx2 = cfd_python.has_avx2()
    has_neon = cfd_python.has_neon()
    has_any_simd = cfd_python.has_simd()

    print("\n   Feature Support:")
    print(f"     AVX2:  {'Yes' if has_avx2 else 'No'}")
    print(f"     NEON:  {'Yes' if has_neon else 'No'}")
    print(f"     Any SIMD: {'Yes' if has_any_simd else 'No'}")

    # SIMD constant mapping
    print("\n   SIMD Constants:")
    print(f"     SIMD_NONE = {cfd_python.SIMD_NONE}")
    print(f"     SIMD_AVX2 = {cfd_python.SIMD_AVX2}")
    print(f"     SIMD_NEON = {cfd_python.SIMD_NEON}")

    # =================================================================
    # 2. Solver Backend Availability
    # =================================================================
    print("\n2. Solver Backend Availability")
    print("-" * 60)

    # Get all available backends
    available_backends = cfd_python.get_available_backends()
    print(f"   Available backends: {available_backends}")

    # Check each backend
    backends = [
        ("SCALAR", cfd_python.BACKEND_SCALAR),
        ("SIMD", cfd_python.BACKEND_SIMD),
        ("OMP", cfd_python.BACKEND_OMP),
        ("CUDA", cfd_python.BACKEND_CUDA),
    ]

    print("\n   Backend details:")
    for name, backend_id in backends:
        available = cfd_python.backend_is_available(backend_id)
        backend_name = cfd_python.backend_get_name(backend_id)
        status = "Available" if available else "Not available"
        print(f"     {name} ({backend_name}): {status}")

    # =================================================================
    # 3. Solvers by Backend
    # =================================================================
    print("\n3. Solvers by Backend")
    print("-" * 60)

    for name, backend_id in backends:
        if cfd_python.backend_is_available(backend_id):
            solvers = cfd_python.list_solvers_by_backend(backend_id)
            backend_name = cfd_python.backend_get_name(backend_id)
            if solvers:
                print(f"\n   {backend_name.upper()} backend solvers:")
                for solver in solvers:
                    print(f"     - {solver}")
            else:
                print(f"\n   {backend_name.upper()}: No solvers registered")

    # =================================================================
    # 4. All Available Solvers
    # =================================================================
    print("\n4. All Available Solvers")
    print("-" * 60)

    all_solvers = cfd_python.list_solvers()
    print(f"   Total solvers: {len(all_solvers)}")
    for solver in all_solvers:
        info = cfd_python.get_solver_info(solver)
        print(f"\n   {solver}:")
        print(f"     Description: {info.get('description', 'N/A')}")
        print(f"     Version: {info.get('version', 'N/A')}")

    # =================================================================
    # 5. Boundary Condition Backends
    # =================================================================
    print("\n5. Boundary Condition Backends")
    print("-" * 60)

    bc_backends = [
        ("AUTO", cfd_python.BC_BACKEND_AUTO),
        ("SCALAR", cfd_python.BC_BACKEND_SCALAR),
        ("OMP", cfd_python.BC_BACKEND_OMP),
        ("SIMD", cfd_python.BC_BACKEND_SIMD),
        ("CUDA", cfd_python.BC_BACKEND_CUDA),
    ]

    current_bc = cfd_python.bc_get_backend()
    current_bc_name = cfd_python.bc_get_backend_name()
    print(f"   Current BC backend: {current_bc_name}")

    print("\n   BC backend availability:")
    for name, backend_id in bc_backends:
        available = cfd_python.bc_backend_available(backend_id)
        status = "Available" if available else "Not available"
        marker = " (current)" if backend_id == current_bc else ""
        print(f"     BC_BACKEND_{name}: {status}{marker}")

    # =================================================================
    # 6. Selecting Optimal Backend
    # =================================================================
    print("\n6. Selecting Optimal Backend")
    print("-" * 60)

    # Determine best available backend
    if cfd_python.backend_is_available(cfd_python.BACKEND_CUDA):
        best = "CUDA"
    elif cfd_python.backend_is_available(cfd_python.BACKEND_SIMD):
        best = "SIMD"
    elif cfd_python.backend_is_available(cfd_python.BACKEND_OMP):
        best = "OpenMP"
    else:
        best = "Scalar"

    print(f"   Recommended solver backend: {best}")

    # Set BC backend based on availability
    if cfd_python.bc_backend_available(cfd_python.BC_BACKEND_SIMD):
        cfd_python.bc_set_backend(cfd_python.BC_BACKEND_SIMD)
        print(f"   Set BC backend to: {cfd_python.bc_get_backend_name()}")
    elif cfd_python.bc_backend_available(cfd_python.BC_BACKEND_OMP):
        cfd_python.bc_set_backend(cfd_python.BC_BACKEND_OMP)
        print(f"   Set BC backend to: {cfd_python.bc_get_backend_name()}")

    # =================================================================
    # 7. Performance Recommendations
    # =================================================================
    print("\n7. Performance Recommendations")
    print("-" * 60)

    recommendations = []

    if has_avx2:
        recommendations.append("Use SIMD backend for vectorized operations (4x speedup)")
    if cfd_python.backend_is_available(cfd_python.BACKEND_OMP):
        recommendations.append("Use OpenMP backend for multi-core parallelization")
    if cfd_python.backend_is_available(cfd_python.BACKEND_CUDA):
        recommendations.append("Use CUDA backend for GPU acceleration (10-100x speedup)")

    if not recommendations:
        recommendations.append("Only scalar backend available - consider building with SIMD/OpenMP")

    print("   Based on your system configuration:")
    for rec in recommendations:
        print(f"     - {rec}")

    # =================================================================
    # Summary
    # =================================================================
    print("\n" + "=" * 60)
    print("Summary")
    print("-" * 60)
    print(f"   CPU SIMD: {arch_name}")
    print(f"   Solver backends: {', '.join(available_backends)}")
    print(f"   BC backend: {cfd_python.bc_get_backend_name()}")
    print(f"   Total solvers: {len(all_solvers)}")


if __name__ == "__main__":
    main()
