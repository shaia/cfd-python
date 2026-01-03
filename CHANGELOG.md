# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Backend Availability API (Phase 5)

- `BACKEND_SCALAR`, `BACKEND_SIMD`, `BACKEND_OMP`, `BACKEND_CUDA` constants
- `backend_is_available(backend)` - Check if backend is available at runtime
- `backend_get_name(backend)` - Get human-readable backend name
- `list_solvers_by_backend(backend)` - List solvers for specific backend
- `get_available_backends()` - List all available backend names

#### Derived Fields & Statistics (Phase 3)

- `calculate_field_stats(data)` - Compute min, max, avg, sum for a field
- `compute_velocity_magnitude(u, v, nx, ny)` - Compute velocity magnitude field
- `compute_flow_statistics(u, v, p, nx, ny)` - Comprehensive flow statistics

#### Error Handling API (Phase 4)

- Python exception hierarchy: `CFDError`, `CFDMemoryError`, `CFDInvalidError`, `CFDIOError`, `CFDUnsupportedError`, `CFDDivergedError`, `CFDMaxIterError`
- `raise_for_status(status_code, context)` - Raise appropriate exception for status codes
- Exception classes integrate with Python standard exceptions (e.g., `CFDMemoryError` inherits from `MemoryError`)

#### CPU Features Detection (Phase 6)

- `SIMD_NONE`, `SIMD_AVX2`, `SIMD_NEON` constants
- `get_simd_arch()` - Get SIMD architecture constant
- `get_simd_name()` - Get SIMD architecture name ("avx2", "neon", "none")
- `has_avx2()`, `has_neon()`, `has_simd()` - Check CPU SIMD capabilities
- `create_grid_stretched(nx, ny, xmin, xmax, ymin, ymax, beta)` - Stretched grid with hyperbolic cosine distribution

#### CI/Build System (Phase 2.5)

- Dual-variant wheel builds supporting both CPU-only and CUDA-enabled configurations
- Matrix build strategy in CI for separate CPU and CUDA wheel artifacts
- Support for CFD library v0.1.6 modular backend libraries

#### Documentation & Examples (Phase 7)

- Comprehensive README with full API reference
- New example scripts demonstrating cfd_python features:
  - `lid_driven_cavity_advanced.py`: Complete cavity simulation with convergence monitoring
  - `channel_flow.py`: Channel flow with parabolic inlet and analytical validation
  - `vtk_output.py`: VTK output for ParaView visualization
  - `solver_comparison.py`: Backend performance comparison and benchmarking
  - `backend_detection.py`: CPU feature and backend availability detection
  - `boundary_conditions.py`: Boundary condition API usage patterns
  - `derived_fields.py`: Computing velocity magnitude and flow statistics
  - `error_handling.py`: Error handling best practices
- New test suites:
  - `test_backend_availability.py` - Backend constants and functions
  - `test_derived_fields.py` - Statistics and velocity magnitude
  - `test_errors.py` - Exception classes and raise_for_status
  - `test_cpu_features.py` - SIMD detection and grid stretching
  - `test_abi_compatibility.py` - NULL handling and stress tests

### Changed
- Updated build system to link modular CFD libraries (cfd_api, cfd_core, cfd_scalar, cfd_simd, cfd_omp, cfd_cuda)
- Migrated to CUDA 12.0.0 from 12.6.2 for better stability and compatibility
- Switched from `uv pip` to standard `pip` for wheel installation in CI tests
- Updated CMakeLists.txt to use GNU linker groups on Linux for circular dependency resolution

### Fixed
- CMake library detection for CFD v0.1.6 static builds
- Wheel installation compatibility with Python stable ABI (abi3) wheels
- Removed non-standard wheel filename modifications for PEP 427 compliance
- CUDA toolkit installation by installing GCC 11 before CUDA on Linux
- Simplified CUDA toolkit installation by removing sub-packages parameter
- Test code style: moved pytest imports to module level for consistency

## [0.1.0] - 2025-12-26

### Added
- Initial Python bindings for CFD library v0.1.5
- Core simulation API bindings (create, step, destroy)
- Solver registry and solver creation
- Grid management functions
- Boundary condition API (periodic, neumann, dirichlet, noslip, inlet, outlet)
- Backend selection for boundary conditions (scalar, SIMD, OpenMP, CUDA)
- Error handling API
- Basic test suite
- GitHub Actions CI/CD pipeline

### Changed
- Updated to CFD library v0.1.5 API (context-bound registry, new type names)
- Migrated from bundled headers to system-installed CFD library

### Technical Details
- Python 3.9+ support using stable ABI (abi3)
- Static linking of CFD library into extension module
- NumPy integration for array handling
- scikit-build-core for modern build system
