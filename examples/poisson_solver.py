#!/usr/bin/env python3
"""
Poisson Solver Example (v0.2.0)

Demonstrates the dedicated Poisson solver subsystem introduced in v0.2.0.
The pressure Poisson equation is the most computationally expensive part of
incompressible flow solvers — choosing the right method and backend matters.

Available methods:
- Jacobi: Simple, parallelizable, slow convergence
- Gauss-Seidel: Faster convergence, sequential
- SOR (Successive Over-Relaxation): Accelerated Gauss-Seidel
- Red-Black SOR: Parallelizable SOR variant
- CG (Conjugate Gradient): Krylov method, good for symmetric systems
- BiCGSTAB: Krylov method for non-symmetric systems
- Multigrid: Optimal O(n) complexity

Backends: Scalar, SIMD, OpenMP, GPU — each accelerates different methods.
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
    print("CFD Python Poisson Solver Example (v0.2.0)")
    print("=" * 60)

    # =================================================================
    # 1. Default Poisson Parameters
    # =================================================================
    print("\n1. Default Poisson Parameters")
    print("-" * 60)

    params = cfd_python.get_default_poisson_params()
    print(f"   Tolerance:          {params.get('tolerance', 'N/A')}")
    print(f"   Abs. tolerance:     {params.get('absolute_tolerance', 'N/A')}")
    print(f"   Max iterations:     {params.get('max_iterations', 'N/A')}")
    print(f"   Omega (SOR):        {params.get('omega', 'N/A')}")
    print(f"   Check interval:     {params.get('check_interval', 'N/A')}")
    print(f"   Verbose:            {params.get('verbose', 'N/A')}")
    print(f"   Preconditioner:     {params.get('preconditioner', 'N/A')}")

    # =================================================================
    # 2. Poisson Solver Methods
    # =================================================================
    print("\n2. Poisson Solver Methods")
    print("-" * 60)

    methods = [
        ("Jacobi", cfd_python.POISSON_METHOD_JACOBI, "Simple iterative, highly parallelizable"),
        (
            "Gauss-Seidel",
            cfd_python.POISSON_METHOD_GAUSS_SEIDEL,
            "Sequential, faster convergence than Jacobi",
        ),
        ("SOR", cfd_python.POISSON_METHOD_SOR, "Accelerated Gauss-Seidel with relaxation"),
        (
            "Red-Black SOR",
            cfd_python.POISSON_METHOD_REDBLACK_SOR,
            "Parallelizable SOR using checkerboard ordering",
        ),
        (
            "Conjugate Gradient",
            cfd_python.POISSON_METHOD_CG,
            "Krylov method, good for large sparse systems",
        ),
        ("BiCGSTAB", cfd_python.POISSON_METHOD_BICGSTAB, "Stabilized bi-conjugate gradient"),
        (
            "Multigrid",
            cfd_python.POISSON_METHOD_MULTIGRID,
            "Optimal O(n) solver using grid hierarchy",
        ),
    ]

    for name, method_id, description in methods:
        print(f"   {name} (id={method_id})")
        print(f"     {description}")

    # =================================================================
    # 3. Poisson Solver Backends
    # =================================================================
    print("\n3. Poisson Solver Backends")
    print("-" * 60)

    backends = [
        ("AUTO", cfd_python.POISSON_BACKEND_AUTO),
        ("SCALAR", cfd_python.POISSON_BACKEND_SCALAR),
        ("OMP", cfd_python.POISSON_BACKEND_OMP),
        ("SIMD", cfd_python.POISSON_BACKEND_SIMD),
        ("GPU", cfd_python.POISSON_BACKEND_GPU),
    ]

    current = cfd_python.poisson_get_backend()
    current_name = cfd_python.poisson_get_backend_name()
    print(f"   Current backend: {current_name}")

    print("\n   Backend availability:")
    for name, backend_id in backends:
        available = cfd_python.poisson_backend_available(backend_id)
        status = "Available" if available else "Not available"
        marker = " (current)" if backend_id == current else ""
        print(f"     POISSON_BACKEND_{name}: {status}{marker}")

    # SIMD-specific check
    simd_avail = cfd_python.poisson_simd_available()
    print(f"\n   SIMD-accelerated Poisson: {'Yes' if simd_avail else 'No'}")

    # =================================================================
    # 4. Solver Presets
    # =================================================================
    print("\n4. Solver Presets (method + backend combinations)")
    print("-" * 60)

    presets = [
        ("SOR + Scalar", cfd_python.POISSON_SOLVER_SOR_SCALAR),
        ("Jacobi + SIMD", cfd_python.POISSON_SOLVER_JACOBI_SIMD),
        ("Red-Black + SIMD", cfd_python.POISSON_SOLVER_REDBLACK_SIMD),
        ("Red-Black + OMP", cfd_python.POISSON_SOLVER_REDBLACK_OMP),
        ("Red-Black + Scalar", cfd_python.POISSON_SOLVER_REDBLACK_SCALAR),
        ("CG + Scalar", cfd_python.POISSON_SOLVER_CG_SCALAR),
        ("CG + SIMD", cfd_python.POISSON_SOLVER_CG_SIMD),
        ("CG + OMP", cfd_python.POISSON_SOLVER_CG_OMP),
    ]

    for name, preset_id in presets:
        print(f"   {name:25s} (id={preset_id})")

    # =================================================================
    # 5. Preconditioners
    # =================================================================
    print("\n5. Preconditioners")
    print("-" * 60)
    print(f"   POISSON_PRECOND_NONE    = {cfd_python.POISSON_PRECOND_NONE}")
    print(f"   POISSON_PRECOND_JACOBI  = {cfd_python.POISSON_PRECOND_JACOBI}")
    print("   Jacobi preconditioning improves CG/BiCGSTAB convergence")

    # =================================================================
    # 6. Selecting a Backend
    # =================================================================
    print("\n6. Selecting a Backend")
    print("-" * 60)

    # Try to set the best available backend
    preferred = [
        ("SIMD", cfd_python.POISSON_BACKEND_SIMD),
        ("OMP", cfd_python.POISSON_BACKEND_OMP),
        ("SCALAR", cfd_python.POISSON_BACKEND_SCALAR),
    ]

    for name, backend_id in preferred:
        if cfd_python.poisson_backend_available(backend_id):
            success = cfd_python.poisson_set_backend(backend_id)
            if success:
                print(f"   Set Poisson backend to: {cfd_python.poisson_get_backend_name()}")
                break
    else:
        print("   Using default backend")

    # =================================================================
    # 7. Choosing the Right Method
    # =================================================================
    print("\n7. Choosing the Right Method")
    print("-" * 60)
    print("   Recommendation guide:")
    print("     Small grids (<64x64):     SOR or Gauss-Seidel")
    print("     Medium grids (64-256):    Red-Black SOR or CG")
    print("     Large grids (>256):       Multigrid or CG with preconditioner")
    print("     GPU available:            CG or Red-Black SOR on GPU")
    print("     SIMD available:           Red-Black SOR or Jacobi with SIMD")

    # =================================================================
    # Summary
    # =================================================================
    print("\n" + "=" * 60)
    print("Summary")
    print("-" * 60)
    print(f"   Methods available: {len(methods)}")
    print(f"   Current backend:   {cfd_python.poisson_get_backend_name()}")
    print(f"   SIMD Poisson:      {'Yes' if simd_avail else 'No'}")
    print(f"   Presets available:  {len(presets)}")


if __name__ == "__main__":
    main()
