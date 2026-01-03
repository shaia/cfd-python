# CFD-Python Migration Plan

This document outlines the required changes to update cfd-python bindings to work with CFD library v0.1.6.

## Current State

- **cfd-python version:** 0.1.0 (outdated)
- **Target CFD library:** v0.1.6
- **Status:** BROKEN - will not compile against current CFD library

## What's New in v0.1.6

CFD library v0.1.6 introduces **Modular Backend Libraries** - a major architectural change that splits the library into separate per-backend components:

- `cfd_core` - Grid, memory, I/O, utilities (base library)
- `cfd_scalar` - Scalar CPU solvers (baseline implementation)
- `cfd_simd` - AVX2/NEON optimized solvers
- `cfd_omp` - OpenMP parallelized solvers (with stubs when OpenMP unavailable)
- `cfd_cuda` - CUDA GPU solvers (conditional compilation)
- `cfd_api` - Dispatcher layer and high-level API (links all backends)
- `cfd_library` - Unified library (all backends, backward compatible)

**Key Changes:**
- Backend availability API for runtime detection
- `ns_solver_backend_t` enum with `SCALAR`, `SIMD`, `OMP`, `CUDA` values
- New functions: `cfd_backend_is_available()`, `cfd_backend_get_name()`, `cfd_registry_list_by_backend()`, `cfd_solver_create_checked()`
- Improved error codes: `CFD_ERROR_UNSUPPORTED` for unavailable backends

**Impact on cfd-python:**
- No breaking API changes (maintains v0.1.5 compatibility)
- Can now query available backends at runtime
- Better error messages when backends unavailable
- Same linking approach (use `cfd_library` or `CFD::Library` CMake target)

## Breaking Changes Summary

### 1. Type Name Changes

All type names have been changed to follow C naming conventions:

| Old (cfd-python) | New (CFD v0.1.6) |
|------------------|------------------|
| `FlowField` | `flow_field` |
| `Grid` | `grid` |
| `SolverParams` | `ns_solver_params_t` |
| `SolverStats` | `ns_solver_stats_t` |
| `Solver` | `ns_solver_t` |
| `SolverStatus` | `cfd_status_t` |
| `SolverCapabilities` | `ns_solver_capabilities_t` |
| `OutputRegistry` | `output_registry` |
| `SimulationData` | `simulation_data` |

### 2. Solver Registry API Changes

**Old (Global Singleton):**
```c
void solver_registry_init(void);
Solver* solver_create(const char* type_name);
int solver_registry_list(const char** names, int max_count);
```

**New (Context-Bound):**
```c
ns_solver_registry_t* cfd_registry_create(void);
void cfd_registry_destroy(ns_solver_registry_t* registry);
void cfd_registry_register_defaults(ns_solver_registry_t* registry);
ns_solver_t* cfd_solver_create(ns_solver_registry_t* registry, const char* type_name);
int cfd_registry_list(ns_solver_registry_t* registry, const char** names, int max_count);
```

### 3. Error Handling Changes

**Old:**
```c
typedef enum { SOLVER_STATUS_OK, SOLVER_STATUS_ERROR, ... } SolverStatus;
```

**New:**
```c
typedef enum { CFD_SUCCESS, CFD_ERROR_NOMEM, CFD_ERROR_INVALID, ... } cfd_status_t;

// New error functions:
void cfd_set_error(cfd_status_t status, const char* message);
const char* cfd_get_last_error(void);
cfd_status_t cfd_get_last_status(void);
const char* cfd_get_error_string(cfd_status_t status);
void cfd_clear_error(void);
```

### 4. Simulation Data Structure Changes

**New fields added:**
```c
typedef struct {
    // ... existing fields with renamed types ...
    ns_solver_registry_t* registry;  // NEW: context-bound registry
    char output_base_dir[512];       // NEW: output directory
} simulation_data;
```

### 5. Output Enum Changes

```c
// Old
OUTPUT_PRESSURE

// New
OUTPUT_VELOCITY_MAGNITUDE
```

### 6. New Solver Types

New solvers added in v0.1.5+ (inherited by v0.1.6):

- `"explicit_euler_omp"` - OpenMP parallel explicit Euler
- `"projection_omp"` - OpenMP parallel projection
- `"conjugate_gradient"` - CG linear solver (internal)

### 7. Backend Availability API (v0.1.6)

New in v0.1.6 for runtime backend detection:

```c
// Backend enum
typedef enum {
    NS_SOLVER_BACKEND_SCALAR = 0,
    NS_SOLVER_BACKEND_SIMD = 1,
    NS_SOLVER_BACKEND_OMP = 2,
    NS_SOLVER_BACKEND_CUDA = 3
} ns_solver_backend_t;

// Backend availability functions
bool cfd_backend_is_available(ns_solver_backend_t backend);
const char* cfd_backend_get_name(ns_solver_backend_t backend);
int cfd_registry_list_by_backend(ns_solver_registry_t* registry,
                                  ns_solver_backend_t backend,
                                  const char** names,
                                  int max_count);
ns_solver_t* cfd_solver_create_checked(ns_solver_registry_t* registry,
                                        const char* type_name);
```

---

## Missing Features

### Boundary Conditions (Completely Missing)

The CFD library has a comprehensive BC API that is not exposed:

**BC Types:**
- `BC_TYPE_PERIODIC` - Periodic boundaries
- `BC_TYPE_NEUMANN` - Zero-gradient
- `BC_TYPE_DIRICHLET` - Fixed value
- `BC_TYPE_NOSLIP` - No-slip walls
- `BC_TYPE_INLET` - Inlet velocity
- `BC_TYPE_OUTLET` - Outlet conditions

**Functions to expose:**
```c
// Core BC functions
cfd_status_t bc_apply_periodic(flow_field* field, bc_edge_t edge);
cfd_status_t bc_apply_neumann(flow_field* field, bc_edge_t edge);
cfd_status_t bc_apply_dirichlet_scalar(double* field, ...);
cfd_status_t bc_apply_dirichlet_velocity(flow_field* field, ...);
cfd_status_t bc_apply_noslip(flow_field* field, bc_edge_t edge);
cfd_status_t bc_apply_inlet(flow_field* field, bc_edge_t edge, const bc_inlet_config_t* config);
cfd_status_t bc_apply_outlet_scalar(double* field, ...);
cfd_status_t bc_apply_outlet_velocity(flow_field* field, ...);

// Backend control
cfd_status_t bc_set_backend(bc_backend_t backend);
bc_backend_t bc_get_backend(void);
bool bc_backend_available(bc_backend_t backend);

// Inlet configuration helpers
bc_inlet_config_t bc_inlet_config_uniform(double u, double v);
bc_inlet_config_t bc_inlet_config_parabolic(double u_max, double v_max);
bc_inlet_config_t bc_inlet_config_custom(bc_velocity_profile_func profile, void* user_data);

// Outlet configuration helpers
bc_outlet_config_t bc_outlet_config_zero_gradient(void);
bc_outlet_config_t bc_outlet_config_convective(double advection_velocity);
```

### Derived Fields & Statistics (Missing)

```c
// Field statistics structure
typedef struct {
    double min_val;
    double max_val;
    double avg_val;
    double sum_val;
} field_stats;

// Derived fields container
derived_fields* derived_fields_create(size_t nx, size_t ny);
void derived_fields_destroy(derived_fields* derived);
void derived_fields_compute_velocity_magnitude(derived_fields* derived, const flow_field* field);
void derived_fields_compute_statistics(derived_fields* derived, const flow_field* field);
```

### CPU Features Detection (Missing)

```c
typedef enum {
    CPU_FEATURE_NONE = 0,
    CPU_FEATURE_SSE2 = (1 << 0),
    CPU_FEATURE_AVX = (1 << 1),
    CPU_FEATURE_AVX2 = (1 << 2),
    CPU_FEATURE_NEON = (1 << 3),
} cpu_features_t;

cpu_features_t cfd_get_cpu_features(void);
```

---

## Migration Plan

### Phase 1: Fix Breaking Changes (Critical) ✅ COMPLETED

**Priority:** P0 - Must complete before any other work

**Status:** Completed on 2025-12-26

**Tasks:**

- [x] **1.1 Update bundled headers or remove them**
  - Chose Option A: Removed bundled headers, require installed CFD library
  - Deleted `src/cfd_lib/` directory

- [x] **1.2 Update type definitions in cfd_python.c**
  - Replaced all `FlowField` → `flow_field`
  - Replaced all `Grid` → `grid`
  - Replaced all `SolverParams` → `ns_solver_params_t`
  - Replaced all `SolverStats` → `ns_solver_stats_t`
  - Replaced all `Solver` → `ns_solver_t`
  - Replaced all `SimulationData` → `simulation_data`

- [x] **1.3 Update solver registry code**
  - Added module-level `g_registry` handle
  - Updated to use `cfd_registry_create()` and `cfd_registry_register_defaults()`
  - Updated `cfd_solver_create()` and `cfd_registry_list()` calls

- [x] **1.4 Update error handling**
  - Replaced with `cfd_status_t` error codes
  - Added error handling API: `get_last_error()`, `get_last_status()`, `get_error_string()`, `clear_error()`
  - Exposed CFD_SUCCESS, CFD_ERROR, CFD_ERROR_* constants to Python

- [x] **1.5 Update simulation API calls**
  - Updated function signatures to match new API
  - Uses `derived_fields` for velocity magnitude computation

- [x] **1.6 Fix output enum**
  - Replaced `OUTPUT_PRESSURE` with `OUTPUT_VELOCITY_MAGNITUDE`

- [x] **1.7 Update CMakeLists.txt**
  - Added CFD library version check (require >= 0.1.6)
  - Added `CFD_BUILD_INCLUDE_DIR` for generated export header
  - Find CFD library headers in correct paths
  - Link modular backend libraries (cfd_api, cfd_core, cfd_scalar, cfd_simd, cfd_omp, cfd_cuda)
  - Added GNU linker groups on Linux for circular dependency resolution
  - Automatic CUDA library detection for optional GPU support

**Actual effort:** 1 day

### Phase 2: Add Boundary Condition Bindings (Important) ✅ COMPLETED

**Priority:** P1 - Required for useful Python API

**Status:** Completed on 2025-12-26

**Tasks:**

- [x] **2.1 Create BC type enums for Python**
  - Added BC_TYPE_* constants (PERIODIC, NEUMANN, DIRICHLET, NOSLIP, INLET, OUTLET)
  - Added BC_EDGE_* constants (LEFT, RIGHT, BOTTOM, TOP)
  - Added BC_BACKEND_* constants (AUTO, SCALAR, OMP, SIMD, CUDA)

- [x] **2.2 Implement core BC wrapper functions**
  - `bc_apply_scalar(field, nx, ny, bc_type)` - Apply BC to scalar field
  - `bc_apply_velocity(u, v, nx, ny, bc_type)` - Apply BC to velocity fields
  - `bc_apply_dirichlet(field, nx, ny, left, right, bottom, top)` - Fixed value BC
  - `bc_apply_noslip(u, v, nx, ny)` - Zero velocity at walls

- [x] **2.3 Implement inlet BC wrappers**
  - `bc_apply_inlet_uniform(u, v, nx, ny, u_inlet, v_inlet, edge)` - Uniform inlet
  - `bc_apply_inlet_parabolic(u, v, nx, ny, max_velocity, edge)` - Parabolic profile

- [x] **2.4 Implement outlet BC wrappers**
  - `bc_apply_outlet_scalar(field, nx, ny, edge)` - Zero-gradient outlet
  - `bc_apply_outlet_velocity(u, v, nx, ny, edge)` - Zero-gradient outlet

- [x] **2.5 Implement backend control**
  - `bc_set_backend(backend)` - Set active backend
  - `bc_get_backend()` - Get current backend
  - `bc_get_backend_name()` - Get backend name string
  - `bc_backend_available(backend)` - Check availability

- [x] **2.6 Add BC tests**
  - Tested all BC types (Neumann, Dirichlet, no-slip)
  - Verified backend detection (OMP available, SIMD detected)
  - All tests pass

**Actual effort:** 1 day

### Phase 2.5: CI/Build System for v0.1.6 (Critical) ✅ COMPLETED

**Priority:** P0 - Required for v0.1.6 compatibility

**Status:** Completed on 2025-12-29

**Tasks:**

- [x] **2.5.1 Implement dual-variant wheel builds**
  - Matrix build strategy for CPU-only and CUDA-enabled wheels
  - CPU wheels: Linux, macOS, Windows (Scalar + SIMD + OpenMP backends)
  - CUDA wheels: Linux, Windows (All CPU backends + CUDA, Turing+ GPUs)
  - Artifact naming: `wheel-{os}-{variant}` for differentiation

- [x] **2.5.2 Fix CMakeLists.txt for modular libraries**
  - Link all modular CFD libraries individually
  - GNU linker groups on Linux for circular dependencies
  - Automatic CUDA library detection

- [x] **2.5.3 Update CI test infrastructure**
  - Install CUDA runtime (12.4.0) for CUDA wheel tests
  - Use standard `pip` instead of `uv` for stable ABI wheel installation
  - Test matrix: Python 3.9 and 3.13 on all platforms
  - Use apt-based CUDA installation on Linux (more reliable than runfile)

- [x] **2.5.4 Ensure PEP 427 compliance**
  - Standard wheel filenames (no variant suffixes)
  - Variant differentiation through artifact names only
  - PyPI-compatible wheel naming

**Actual effort:** 1 day

### Phase 3: Add Derived Fields & Statistics (Important) ✅ COMPLETED

**Priority:** P1 - Useful for post-processing

**Status:** Completed on 2026-01-01

**Tasks:**

- [x] **3.1 Implement field statistics function**
  - `calculate_field_stats(data)` - Compute min, max, avg, sum for a field
  - Returns dict with 'min', 'max', 'avg', 'sum' keys

- [x] **3.2 Implement velocity magnitude computation**
  - `compute_velocity_magnitude(u, v, nx, ny)` - Compute sqrt(u^2 + v^2)
  - Returns list of velocity magnitudes

- [x] **3.3 Implement comprehensive flow statistics**
  - `compute_flow_statistics(u, v, p, nx, ny)` - Statistics for all flow components
  - Returns dict with 'u', 'v', 'p', 'velocity_magnitude' stats

- [x] **3.4 Add tests**
  - Created `tests/test_derived_fields.py` with comprehensive tests
  - Tests for all three functions with edge cases
  - Proper error handling tests (empty lists, wrong types, size mismatches)

**Actual effort:** < 1 day

### Phase 4: Add Error Handling API (Important) ✅ COMPLETED

**Priority:** P1 - Better debugging

**Status:** Completed on 2026-01-02

**Tasks:**

- [x] **4.1 Expose error functions**
  - `get_last_error()` → Python string (already in C extension)
  - `get_last_status()` → Python enum (already in C extension)
  - `get_error_string(code)` → Python string (already in C extension)
  - `clear_error()` (already in C extension)

- [x] **4.2 Create Python exceptions**
  - Created `cfd_python/_exceptions.py` with exception hierarchy
  - `CFDError` base exception with `status_code` and `message` attributes
  - `CFDMemoryError(CFDError, MemoryError)` - for CFD_ERROR_NOMEM (-2)
  - `CFDInvalidError(CFDError, ValueError)` - for CFD_ERROR_INVALID (-3)
  - `CFDIOError(CFDError, IOError)` - for CFD_ERROR_IO (-4)
  - `CFDUnsupportedError(CFDError, NotImplementedError)` - for CFD_ERROR_UNSUPPORTED (-5)
  - `CFDDivergedError(CFDError)` - for CFD_ERROR_DIVERGED (-6)
  - `CFDMaxIterError(CFDError)` - for CFD_ERROR_MAX_ITER (-7)

- [x] **4.3 Implement raise_for_status helper**
  - `raise_for_status(status_code, context="")` - Raises appropriate exception based on status code
  - Maps status codes to exception classes
  - Includes error message from C library when available

- [x] **4.4 Add tests**
  - Added tests to `tests/test_errors.py`
  - Tests for exception class hierarchy and inheritance
  - Tests for `raise_for_status` function with all error codes
  - Tests for export verification

**Actual effort:** < 0.5 days

### Phase 5: Add Backend Availability API (v0.1.6 Feature) ✅ COMPLETED

**Priority:** P1 - Important for v0.1.6 compatibility

**Status:** Completed on 2025-12-31

**Tasks:**

- [x] **5.1 Expose backend enum**
  - Added `BACKEND_SCALAR`, `BACKEND_SIMD`, `BACKEND_OMP`, `BACKEND_CUDA` constants
  - Map to `ns_solver_backend_t` enum (values 0-3)

- [x] **5.2 Implement backend availability functions**
  - `backend_is_available(backend)` → bool
  - `backend_get_name(backend)` → string
  - `list_solvers_by_backend(backend)` → list of solver names

- [x] **5.3 Add backend query helpers**
  - `get_available_backends()` → list of available backend names

- [x] **5.4 Add tests**
  - Created `tests/test_backend_availability.py` with comprehensive tests
  - Tests for constants, availability checking, name queries, solver listing

**Note:** `create_solver_checked()` and `get_solver_backend()` deferred to Phase 4 (error handling integration).

**Actual effort:** 0.5 days

### Phase 6: Add CPU Features & Misc (Enhancement) ✅ COMPLETED

**Priority:** P2 - Nice to have

**Status:** Completed on 2026-01-02

**Tasks:**

- [x] **6.1 CPU features detection**
  - Added `SIMD_NONE`, `SIMD_AVX2`, `SIMD_NEON` constants
  - `get_simd_arch()` → returns SIMD architecture constant
  - `get_simd_name()` → returns "avx2", "neon", or "none"
  - `has_avx2()` → bool (checks AVX2 availability with OS support verification)
  - `has_neon()` → bool (checks ARM NEON availability)
  - `has_simd()` → bool (checks if any SIMD is available)

- [x] **6.2 Grid initialization variants**
  - `create_grid_stretched(nx, ny, xmin, xmax, ymin, ymax, beta)` - Hyperbolic cosine stretching
  - Clusters points toward the domain center (symmetric stretching)
  - Note: Chebyshev and geometric variants not available in C library

- [x] **6.3 Add tests**
  - Created `tests/test_cpu_features.py` with 26 tests
  - Tests for SIMD constants, detection functions, and grid stretching

**Actual effort:** < 0.5 days

### Phase 7: Documentation & Tests (Required)

**Priority:** P1 - Required for release

**Tasks:**

- [ ] **7.1 Update README**
  - Installation instructions
  - API changes documentation
  - Migration guide for users
  - Backend availability examples

- [ ] **7.2 Update Python docstrings**
  - All new functions
  - BC examples
  - Error handling examples
  - Backend detection examples

- [ ] **7.3 Add comprehensive tests**
  - Test all BC types
  - Test error handling
  - Test derived fields
  - Test with different backends
  - Test backend availability API

- [ ] **7.4 Update examples**
  - BC usage examples
  - Derived fields examples
  - Backend detection examples

**Estimated effort:** 2 days

---

## File Changes Summary

### Files to Modify

| File | Changes |
|------|---------|
| `src/cfd_python.c` | Major rewrite - types, registry, errors, new functions |
| `CMakeLists.txt` | CFD library detection, version check |
| `cfd_python/__init__.py` | Export new functions, enums, exceptions |
| `cfd_python/_loader.py` | No changes expected |
| `pyproject.toml` | Version bump, dependency update |
| `README.md` | Update documentation |

### Files to Remove

| File | Reason |
|------|--------|
| `src/cfd_lib/include/*.h` | Bundled headers - use installed library instead |

### Files to Create

| File | Purpose |
|------|---------|
| `src/boundary_conditions.c` | BC wrapper functions (optional - can be in main file) |
| `tests/test_boundary_conditions.py` | BC tests |
| `tests/test_derived_fields.py` | Derived fields tests |
| `tests/test_error_handling.py` | Error handling tests |
| `tests/test_backend_availability.py` | Backend availability API tests |
| `examples/boundary_conditions.py` | BC usage examples |
| `examples/backend_detection.py` | Backend detection examples |

---

## Dependency Changes

### Build Dependencies

```toml
# pyproject.toml
[build-system]
requires = ["scikit-build-core", "numpy"]

[project]
dependencies = ["numpy>=1.20"]
```

### Runtime Dependencies

- CFD library >= 0.1.6 installed system-wide
- NumPy >= 1.20

### CMake Requirements

```cmake
# Find CFD library (v0.1.6 with modular backend libraries)
find_package(CFD 0.1.6 REQUIRED)

# Link against the unified library (includes all backends)
target_link_libraries(cfd_python PRIVATE CFD::Library)

# Or manual detection
find_path(CFD_INCLUDE_DIR cfd/api/simulation_api.h)
find_library(CFD_LIBRARY cfd_library)  # Unified library name
```

---

## Timeline Estimate

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 1: Breaking Changes | ~~2-3 days~~ ✅ 1 day | ~~2-3 days~~ 1 day |
| Phase 2: Boundary Conditions | ~~3-4 days~~ ✅ 1 day | ~~5-7 days~~ 2 days |
| Phase 2.5: CI/Build System (v0.1.6) | ✅ 1 day | 3 days |
| Phase 3: Derived Fields | ~~1-2 days~~ ✅ < 1 day | 3.5 days |
| Phase 4: Error Handling | ~~1 day~~ ✅ < 0.5 days | 4 days |
| Phase 5: Backend Availability (v0.1.6) | ✅ 0.5 days | 4.5 days |
| Phase 6: CPU Features | ~~1 day~~ ✅ < 0.5 days | 5 days |
| Phase 7: Docs & Tests | 2 days | 7 days |

**Total estimated effort:** ~~9-10 days~~ ~7 days (5 days completed)

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| API changes in CFD library | High | Pin to specific version, add version checks |
| Build system complexity | Medium | Test on all platforms in CI |
| BC backend compatibility | Medium | Test with fallback to scalar backend |
| NumPy ABI compatibility | Low | Use stable ABI, test multiple versions |

---

## Success Criteria

1. All existing tests pass
2. New BC tests pass
3. Backend availability API tests pass
4. Builds successfully on Windows, Linux, macOS
5. Works with CFD library v0.1.6
6. Correctly detects available backends at runtime
7. Python API is Pythonic and well-documented
8. Examples run successfully

---

## Pythonic API Assessment

**Assessment Date:** 2026-01-02

### ✅ What's Pythonic (Good Practices)

**1. Exception Hierarchy Design** - Excellent
- Multiple inheritance with standard Python exceptions (`CFDMemoryError(CFDError, MemoryError)`)
- Enables idiomatic exception handling: `except MemoryError` catches CFD memory errors
- The `raise_for_status()` pattern follows requests library conventions
- Docstrings with attribute documentation

**2. Naming Conventions** - Good
- Functions use `snake_case` (`create_grid`, `run_simulation`, `has_avx2`)
- Constants use `UPPER_CASE` (`SIMD_AVX2`, `BC_TYPE_DIRICHLET`)
- Private modules prefixed with underscore (`_loader.py`, `_exceptions.py`)

**3. Return Types** - Good
- Functions return native Python types (dict, list, bool, int) instead of custom objects
- `create_grid()` returns a dict with intuitive keys (`nx`, `ny`, `x_coords`)
- `run_simulation_with_params()` returns structured dict with `stats` sub-dict

**4. Module Organization** - Good
- Clean `__all__` exports
- Graceful handling of unbuilt extension (`ExtensionNotBuiltError`)
- Dynamic solver constants discovery

### ⚠️ Areas for Improvement

**1. ~~Inconsistent Coordinate Naming~~ (FIXED)**
```python
# Both functions now return consistent keys:
grid["x_coords"], grid["y_coords"]  # standardized naming
```

**2. Mixed Paradigms for Complex Operations**
```python
# Positional args (C-style):
create_grid(10, 10, 0.0, 1.0, 0.0, 1.0)

# More Pythonic alternative:
create_grid(nx=10, ny=10, bounds=(0.0, 1.0, 0.0, 1.0))
# or
create_grid(nx=10, ny=10, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0)
```

**3. Verbose Boundary Condition API**
The BC functions require separate calls for each boundary type. A more Pythonic approach might be:
```python
# Current:
bc_apply_inlet_uniform(u, v, nx, ny, u_inlet, v_inlet, BC_EDGE_LEFT)
bc_apply_outlet_velocity(u, v, nx, ny, BC_EDGE_RIGHT)

# More Pythonic (context manager or builder pattern):
with BoundaryConditions(u, v, nx, ny) as bc:
    bc.left.inlet_uniform(u=1.0, v=0.0)
    bc.right.outlet()
```

**4. Constants Could Use IntEnum**
```python
# Current:
SIMD_NONE = 0
SIMD_AVX2 = 1

# More Pythonic:
class SIMDArch(IntEnum):
    NONE = 0
    AVX2 = 1
    NEON = 2
```
This provides `str(SIMDArch.AVX2)` → `"SIMDArch.AVX2"` and better IDE support.

**5. No Type Hints in Public API**
While `_exceptions.py` has type hints, the C extension functions lack type stubs (`.pyi` files) for IDE autocompletion.

### 📊 Summary

| Aspect | Rating | Notes |
|--------|--------|-------|
| Naming | ★★★★☆ | Follows PEP 8, minor inconsistencies |
| Error Handling | ★★★★★ | Excellent exception hierarchy |
| Return Types | ★★★★☆ | Native types, dict structure could use dataclasses |
| API Design | ★★★☆☆ | Functional but verbose, mirrors C API closely |
| Type Annotations | ★★☆☆☆ | Missing .pyi stubs for C extension |
| Documentation | ★★★★☆ | Good docstrings in `__init__.py` |

**Overall:** The code is reasonably Pythonic for a C extension binding. The exception handling is particularly well-designed. The main improvements would be adding type stubs and potentially providing higher-level Pythonic wrappers around the lower-level C-style functions.

### Recommended Future Enhancements

1. **Add type stubs** (`cfd_python.pyi`) for IDE autocompletion
2. **Standardize coordinate naming** across grid functions
3. **Consider IntEnum** for constant groups (SIMD, BC types, backends)
4. **Optional high-level wrappers** for BC operations (Phase 8 candidate)
