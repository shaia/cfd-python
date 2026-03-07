#!/usr/bin/env python3
"""
GPU Management Example (v0.2.0)

Demonstrates the GPU device management APIs introduced in v0.2.0.
These functions allow querying GPU availability, inspecting device
properties, selecting a specific device for multi-GPU systems,
and retrieving default GPU configuration.

GPU acceleration provides 10-100x speedup for large simulations
by offloading pressure solves and boundary condition computation
to CUDA-capable devices.
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
    print("CFD Python GPU Management Example (v0.2.0)")
    print("=" * 60)

    # =================================================================
    # 1. GPU Availability
    # =================================================================
    print("\n1. GPU Availability")
    print("-" * 60)

    gpu_available = cfd_python.gpu_is_available()
    print(f"   GPU acceleration: {'Available' if gpu_available else 'Not available'}")

    if not gpu_available:
        print("\n   No GPU detected. This example will show the API usage")
        print("   but GPU-specific operations will be skipped.")
        print("\n   To enable GPU support, build with CUDA:")
        print("     pip install -e . --config-settings=cmake.args=-DCFD_ENABLE_CUDA=ON")

    # =================================================================
    # 2. Device Information
    # =================================================================
    print("\n2. Device Information")
    print("-" * 60)

    devices = cfd_python.gpu_get_device_info()

    if devices:
        print(f"   Found {len(devices)} GPU device(s):\n")
        for i, device in enumerate(devices):
            print(f"   Device {i}:")
            for key, value in device.items():
                print(f"     {key}: {value}")
            print()
    else:
        print("   No GPU devices found")

    # =================================================================
    # 3. Device Selection (multi-GPU)
    # =================================================================
    print("\n3. Device Selection")
    print("-" * 60)

    if len(devices) > 1:
        # In multi-GPU systems, select the best device
        print(f"   Multiple GPUs detected ({len(devices)} devices)")
        print("   Selecting device 0...")
        cfd_python.gpu_select_device(0)
        print("   Device 0 selected")

        print("\n   Multi-GPU strategy:")
        print("     - Use gpu_select_device() before creating simulations")
        print("     - Each simulation runs on the selected device")
        print("     - Switch devices between independent simulations")
    elif len(devices) == 1:
        print("   Single GPU detected, using device 0 (default)")
    else:
        print("   No devices to select")
        print("   gpu_select_device(device_id) sets the active GPU")

    # =================================================================
    # 4. Default GPU Configuration
    # =================================================================
    print("\n4. Default GPU Configuration")
    print("-" * 60)

    config = cfd_python.gpu_get_default_config()

    if config:
        for key, value in config.items():
            print(f"   {key}: {value}")
    else:
        print("   No GPU configuration available (GPU not built)")

    # =================================================================
    # 5. GPU + Solver Integration
    # =================================================================
    print("\n5. GPU + Solver Integration")
    print("-" * 60)

    # Check for GPU solvers
    gpu_solvers = []
    for solver in cfd_python.list_solvers():
        if "gpu" in solver.lower() or "cuda" in solver.lower():
            gpu_solvers.append(solver)

    if gpu_solvers:
        print("   GPU-enabled solvers:")
        for solver in gpu_solvers:
            info = cfd_python.get_solver_info(solver)
            print(f"     - {solver}: {info.get('description', 'N/A')}")
    else:
        print("   No GPU solvers available in this build")

    # Check Poisson solver GPU backend
    poisson_gpu = cfd_python.poisson_backend_available(cfd_python.POISSON_BACKEND_GPU)
    print(f"\n   Poisson GPU backend: {'Available' if poisson_gpu else 'Not available'}")

    # Check BC CUDA backend
    bc_cuda = cfd_python.bc_backend_available(cfd_python.BC_BACKEND_CUDA)
    print(f"   BC CUDA backend:     {'Available' if bc_cuda else 'Not available'}")

    # =================================================================
    # 6. Running a GPU Simulation
    # =================================================================
    print("\n6. Running a GPU Simulation")
    print("-" * 60)

    if gpu_available and gpu_solvers:
        print(f"   Using GPU solver: {gpu_solvers[0]}")
        result = cfd_python.run_simulation_with_params(
            nx=32,
            ny=32,
            xmin=0.0,
            xmax=1.0,
            ymin=0.0,
            ymax=1.0,
            steps=10,
            solver_type=gpu_solvers[0],
        )
        print(f"   Completed: {result['nx']}x{result['ny']} grid, {result['steps']} steps")
        print(f"   Solver: {result.get('solver_name', 'N/A')}")
    else:
        print("   GPU solver not available, running CPU simulation instead")
        result = cfd_python.run_simulation(nx=32, ny=32, steps=10)
        print(f"   Completed: {len(result)} points (CPU)")

    # =================================================================
    # Summary
    # =================================================================
    print("\n" + "=" * 60)
    print("Summary")
    print("-" * 60)
    print(f"   GPU available:     {gpu_available}")
    print(f"   Devices found:     {len(devices)}")
    print(f"   GPU solvers:       {len(gpu_solvers)}")
    print(f"   Poisson GPU:       {poisson_gpu}")
    print(f"   BC CUDA:           {bc_cuda}")


if __name__ == "__main__":
    main()
