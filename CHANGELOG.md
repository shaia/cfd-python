# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Dual-variant wheel builds supporting both CPU-only and CUDA-enabled configurations
- Matrix build strategy in CI for separate CPU and CUDA wheel artifacts
- Support for CFD library v0.1.6 modular backend libraries

### Changed
- Updated build system to link modular CFD libraries (cfd_api, cfd_core, cfd_scalar, cfd_simd, cfd_omp, cfd_cuda)
- Migrated to CUDA 12.0.0 from 12.6.2 for better stability and compatibility
- Switched from `uv pip` to standard `pip` for wheel installation in CI tests
- Updated CMakeLists.txt to use GNU linker groups on Linux for circular dependency resolution

### Fixed
- CMake library detection for CFD v0.1.6 static builds
- Wheel installation compatibility with Python stable ABI (abi3) wheels
- Removed non-standard wheel filename modifications for PEP 427 compliance

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
