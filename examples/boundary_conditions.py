#!/usr/bin/env python3
"""
Boundary Conditions Example

This example demonstrates how to use the boundary condition API in cfd_python.
It shows the various BC types, backend selection, and practical usage patterns.
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
    print("CFD Python Boundary Conditions Example")
    print("=" * 60)

    # Grid dimensions
    nx, ny = 20, 20
    size = nx * ny

    # =================================================================
    # 1. BC Backend Information
    # =================================================================
    print("\n1. Boundary Condition Backend Information")
    print("-" * 60)

    # Show current backend
    current_backend = cfd_python.bc_get_backend()
    current_name = cfd_python.bc_get_backend_name()
    print(f"   Current BC backend: {current_name} (id={current_backend})")

    # Check available backends
    backends = [
        ("AUTO", cfd_python.BC_BACKEND_AUTO),
        ("SCALAR", cfd_python.BC_BACKEND_SCALAR),
        ("OMP", cfd_python.BC_BACKEND_OMP),
        ("SIMD", cfd_python.BC_BACKEND_SIMD),
        ("CUDA", cfd_python.BC_BACKEND_CUDA),
    ]

    print("\n   Backend availability:")
    for name, backend_id in backends:
        available = cfd_python.bc_backend_available(backend_id)
        status = "Available" if available else "Not available"
        print(f"     BC_BACKEND_{name}: {status}")

    # =================================================================
    # 2. Neumann (Zero-Gradient) Boundary Conditions
    # =================================================================
    print("\n2. Neumann (Zero-Gradient) Boundary Conditions")
    print("-" * 60)

    # Create a scalar field with a gradient
    pressure = [float(i % nx) for i in range(size)]  # Gradient in x-direction
    print(f"   Initial field: min={min(pressure):.2f}, max={max(pressure):.2f}")

    # Apply Neumann BCs (zero gradient at boundaries)
    cfd_python.bc_apply_scalar(pressure, nx, ny, cfd_python.BC_TYPE_NEUMANN)
    print("   Applied Neumann BC to scalar field")

    # =================================================================
    # 3. Dirichlet (Fixed Value) Boundary Conditions
    # =================================================================
    print("\n3. Dirichlet (Fixed Value) Boundary Conditions")
    print("-" * 60)

    # Create a temperature-like field
    temperature = [0.0] * size

    # Set fixed values at boundaries
    left_val = 100.0  # Hot wall on left
    right_val = 0.0  # Cold wall on right
    bottom_val = 50.0
    top_val = 50.0

    cfd_python.bc_apply_dirichlet(temperature, nx, ny, left_val, right_val, bottom_val, top_val)
    print(f"   Applied Dirichlet BC: left={left_val}, right={right_val}")
    print(f"   Left edge value: {temperature[0]}")
    print(f"   Right edge value: {temperature[nx-1]}")

    # =================================================================
    # 4. No-Slip Wall Boundary Conditions
    # =================================================================
    print("\n4. No-Slip Wall Boundary Conditions")
    print("-" * 60)

    # Create velocity fields with some initial values
    u = [1.0] * size  # Initial u velocity
    v = [0.5] * size  # Initial v velocity

    print(f"   Before no-slip: u[0]={u[0]}, v[0]={v[0]}")

    # Apply no-slip (zero velocity at all walls)
    cfd_python.bc_apply_noslip(u, v, nx, ny)

    print("   Applied no-slip BC to all walls")
    print(f"   After no-slip: u[0]={u[0]}, v[0]={v[0]} (corner)")
    print(f"   Interior: u[{nx+1}]={u[nx+1]}, v[{nx+1}]={v[nx+1]}")

    # =================================================================
    # 5. Inlet Boundary Conditions
    # =================================================================
    print("\n5. Inlet Boundary Conditions")
    print("-" * 60)

    # Reset velocity fields
    u = [0.0] * size
    v = [0.0] * size

    # Uniform inlet on left edge
    u_inlet = 1.0
    v_inlet = 0.0
    cfd_python.bc_apply_inlet_uniform(u, v, nx, ny, u_inlet, v_inlet, cfd_python.BC_EDGE_LEFT)
    print(f"   Applied uniform inlet (u={u_inlet}, v={v_inlet}) on left edge")
    print(f"   Left edge u velocity: {u[0]}")

    # Parabolic inlet on left edge (for channel flow)
    u2 = [0.0] * size
    v2 = [0.0] * size
    max_velocity = 1.5

    cfd_python.bc_apply_inlet_parabolic(u2, v2, nx, ny, max_velocity, cfd_python.BC_EDGE_LEFT)
    print(f"\n   Applied parabolic inlet (max={max_velocity}) on left edge")
    # Check velocity at center vs edge of inlet
    center_idx = (ny // 2) * nx
    edge_idx = 0
    print(f"   Edge velocity: u={u2[edge_idx]:.4f}")
    print(f"   Center velocity: u={u2[center_idx]:.4f}")

    # =================================================================
    # 6. Outlet Boundary Conditions
    # =================================================================
    print("\n6. Outlet Boundary Conditions")
    print("-" * 60)

    # Use existing velocity field and apply outlet on right edge
    cfd_python.bc_apply_outlet_velocity(u, v, nx, ny, cfd_python.BC_EDGE_RIGHT)
    print("   Applied zero-gradient outlet on right edge")

    # Scalar field outlet
    scalar_field = [float(i) for i in range(size)]
    cfd_python.bc_apply_outlet_scalar(scalar_field, nx, ny, cfd_python.BC_EDGE_RIGHT)
    print("   Applied zero-gradient outlet for scalar field")

    # =================================================================
    # 7. Switching Backends
    # =================================================================
    print("\n7. Switching BC Backends")
    print("-" * 60)

    # Try to set OpenMP backend if available
    if cfd_python.bc_backend_available(cfd_python.BC_BACKEND_OMP):
        cfd_python.bc_set_backend(cfd_python.BC_BACKEND_OMP)
        print(f"   Switched to: {cfd_python.bc_get_backend_name()}")

        # Apply BC with new backend
        test_field = [0.0] * size
        cfd_python.bc_apply_scalar(test_field, nx, ny, cfd_python.BC_TYPE_NEUMANN)
        print("   Applied Neumann BC with OpenMP backend")
    else:
        print("   OpenMP backend not available, skipping")

    # Switch back to auto
    cfd_python.bc_set_backend(cfd_python.BC_BACKEND_AUTO)
    print(f"   Reset to: {cfd_python.bc_get_backend_name()}")

    # =================================================================
    # Summary
    # =================================================================
    print("\n" + "=" * 60)
    print("Boundary Condition Types Available:")
    print("  - BC_TYPE_PERIODIC: Periodic boundaries")
    print("  - BC_TYPE_NEUMANN: Zero-gradient (∂φ/∂n = 0)")
    print("  - BC_TYPE_DIRICHLET: Fixed value")
    print("  - BC_TYPE_NOSLIP: Zero velocity at walls")
    print("  - BC_TYPE_INLET: Inlet velocity (uniform/parabolic)")
    print("  - BC_TYPE_OUTLET: Outlet conditions (zero-gradient)")
    print("\nEdge Constants:")
    print("  - BC_EDGE_LEFT, BC_EDGE_RIGHT, BC_EDGE_BOTTOM, BC_EDGE_TOP")


if __name__ == "__main__":
    main()
