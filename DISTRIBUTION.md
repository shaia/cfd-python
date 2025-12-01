# CFD Python Distribution Guide

## Quick Start

**For users:** `pip install cfd-python` (works everywhere)
**For developers:** Push to GitHub -> Automated builds -> PyPI publishing

---

## Distribution Strategy

### Self-Contained Python Package with Static Linking

The cfd-python package uses **static linking** to embed the CFD C library directly into the Python extension. This creates self-contained wheels that don't require users to have the C library installed separately.

```
cfd-workspace/
├── cfd/                      # C library (external, statically linked)
│   ├── lib/include/          # Headers
│   └── build/lib/Release/    # Static library (.a or .lib)
└── cfd-python/               # Python bindings
    ├── pyproject.toml        # Build configuration
    ├── CMakeLists.txt        # CMake build with CFD_STATIC_LINK
    ├── src/cfd_python.c      # Python C extension
    ├── cfd_python/           # Python package
    │   └── __init__.py       # Dynamic solver discovery
    └── tests/                # Test suite
```

**Benefits:**

- One command install: `pip install cfd-python`
- Cross-platform: Windows, macOS, Linux
- No build dependencies for users
- Dynamic solver discovery (new solvers automatically available)
- Static linking means no DLL/shared library issues

---

## Static Linking Configuration

### CMakeLists.txt

The build system uses `CFD_STATIC_LINK` to control linking and `CFD_USE_STABLE_ABI` for Python version compatibility:

```cmake
option(CFD_STATIC_LINK "Statically link the CFD library" ON)
option(CFD_USE_STABLE_ABI "Use Python stable ABI for cross-version compatibility" OFF)

# Static library discovery with platform-specific names
if(CFD_STATIC_LINK)
    if(WIN32)
        find_library(CFD_LIBRARY NAMES cfd_library_static cfd_library ...)
    else()
        find_library(CFD_LIBRARY NAMES libcfd_library.a cfd_library ...)
    endif()
endif()

# Stable ABI support for single-wheel-per-platform builds
if(CFD_USE_STABLE_ABI AND WIN32)
    # Windows: manually link against python3.lib (stable ABI)
    add_library(cfd_python MODULE src/cfd_python.c)
    target_compile_definitions(cfd_python PRIVATE Py_LIMITED_API=0x03080000)
    target_link_libraries(cfd_python PRIVATE ${PYTHON3_STABLE_LIB})
else()
    # Unix: use Python_add_library with .abi3.so suffix
    Python_add_library(cfd_python MODULE WITH_SOABI src/cfd_python.c)
    if(CFD_USE_STABLE_ABI)
        target_compile_definitions(cfd_python PRIVATE Py_LIMITED_API=0x03080000)
        set_target_properties(cfd_python PROPERTIES SUFFIX ".abi3.so")
    endif()
endif()
```

### pyproject.toml

Static linking and stable ABI are enabled in the build configuration:

```toml
[tool.scikit-build]
minimum-version = "0.4"
build-dir = "build/{wheel_tag}"
wheel.py-api = "cp38"  # Target Python 3.8+ stable ABI

[tool.scikit-build.cmake.define]
CMAKE_BUILD_TYPE = "Release"
CFD_STATIC_LINK = "ON"
CFD_USE_STABLE_ABI = "ON"
```

The `wheel.py-api = "cp38"` setting combined with `CFD_USE_STABLE_ABI` produces a single wheel per platform that works with Python 3.8+.

---

## Dynamic Solver Discovery

The Python wrapper automatically discovers all registered solvers from the C library at import time. When new solvers are added to the C library:

1. Register the solver in the C library's solver registry
2. Rebuild the Python extension
3. The new solver is automatically available as `SOLVER_<NAME>` constant

```python
import cfd_python

# List all available solvers
print(cfd_python.list_solvers())
# ['explicit_euler', 'explicit_euler_optimized', 'projection', ...]

# Check for a specific solver
if cfd_python.has_solver('explicit_euler_gpu'):
    print("GPU solver available!")

# Dynamic constants are created automatically
print(cfd_python.SOLVER_EXPLICIT_EULER)  # 'explicit_euler'
```

---

## Building Wheels

### Local Development Build

```bash
# Build the C library first (static)
cd ../cfd
cmake -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
cmake --build build --config Release

# Build and install Python package
cd ../cfd-python
pip install -e .
```

### CI Build Process

The GitHub Actions workflow builds wheels directly using `pip wheel` with the CFD library checked out as a sibling directory. This approach:

- Produces one wheel per platform (stable ABI)
- Works with Python 3.8-3.12+
- Statically links the CFD C library

**Build steps (all platforms):**

1. Checkout cfd-python repository
2. Checkout cfd C library to `./cfd` directory
3. Build CFD library with CMake (static, release)
4. Build wheel with `pip wheel . --no-deps`

**Environment variables:**

- `CFD_ROOT`: Path to CFD C library (set to `./cfd` in CI)
- `CFD_STATIC_LINK=ON`: Enable static linking
- `CFD_USE_STABLE_ABI=ON`: Build for Python stable ABI

---

## CI/CD Pipeline

### GitHub Actions Workflows

The project uses two workflows:

#### build-wheels.yml (Reusable)

Builds and tests wheels on all platforms. Triggered on push, PR, or called by other workflows.

```yaml
name: Build and Test Wheels

on:
  push:
    branches: [main, master]
  pull_request:
  workflow_dispatch:
  workflow_call:  # Allows publish.yml to reuse this workflow

jobs:
  build_wheel:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    steps:
      - uses: actions/checkout@v4
      - name: Checkout CFD C library
        uses: actions/checkout@v4
        with:
          repository: ${{ github.repository_owner }}/cfd
          path: cfd
      - name: Build CFD library
        run: |
          cmake -S cfd -B cfd/build -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
          cmake --build cfd/build --config Release
      - name: Build wheel
        env:
          CFD_ROOT: ${{ github.workspace }}/cfd
          CFD_STATIC_LINK: "ON"
          CFD_USE_STABLE_ABI: "ON"
        run: pip wheel . --no-deps --wheel-dir dist/
      - uses: actions/upload-artifact@v4
        with:
          name: wheel-${{ matrix.os }}
          path: dist/*.whl

  test_wheel:
    needs: [build_wheel]
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python: ["3.8", "3.12"]
    steps:
      # Install wheel, run import test, run pytest
```

#### publish.yml (PyPI Publishing)

Publishes to TestPyPI or PyPI using trusted publishing (OIDC).

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]
  push:
    tags: ['v*']
  workflow_dispatch:
    inputs:
      target:
        type: choice
        options: [testpypi, pypi]

concurrency:
  group: publish-${{ github.ref }}
  cancel-in-progress: false

jobs:
  build:
    uses: ./.github/workflows/build-wheels.yml  # Reuse build workflow

  build_sdist:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python -m build --sdist
      - uses: actions/upload-artifact@v4

  publish_testpypi:
    needs: [build, build_sdist]
    if: github.event_name == 'workflow_dispatch' && github.event.inputs.target == 'testpypi'
    environment: testpypi
    permissions:
      id-token: write  # Required for trusted publishing
    steps:
      - uses: actions/download-artifact@v4
      - name: Validate artifacts
        run: |
          # Ensure at least 3 wheels (linux, macos, windows) and 1 sdist
      - uses: pypa/gh-action-pypi-publish@release/v1
        with:
          repository-url: https://test.pypi.org/legacy/

  publish_pypi:
    needs: [build, build_sdist]
    if: github.event_name == 'release' || startsWith(github.ref, 'refs/tags/v')
    environment: pypi
    permissions:
      id-token: write
    steps:
      - uses: actions/download-artifact@v4
      - uses: pypa/gh-action-pypi-publish@release/v1
```

### Trusted Publishing Setup

The workflows use PyPI trusted publishing (OIDC) instead of API tokens:

1. Go to PyPI/TestPyPI → Your Project → Settings → Publishing
2. Add a new trusted publisher with:
   - Owner: `<your-github-org>`
   - Repository: `cfd-python`
   - Workflow: `publish.yml`
   - Environment: `pypi` or `testpypi`

---

## Distribution Methods Comparison

| Method | User Experience | Maintenance | Best For |
|--------|-----------------|-------------|----------|
| **PyPI Wheels** | `pip install cfd-python` | Automated CI/CD | Everyone |
| **Conda Package** | `conda install cfd-python` | Manual recipe | Scientists |
| **Docker Image** | `docker run cfd-python` | Image maintenance | Reproducible research |
| **Source Build** | Complex setup required | User support issues | Developers only |

---

## Testing Installation

```bash
# Install from wheel
pip install wheelhouse/cfd_python-*.whl

# Verify installation
python -c "import cfd_python; print(cfd_python.__version__)"

# List available solvers
python -c "import cfd_python; print(cfd_python.list_solvers())"

# Run a quick test
python -c "import cfd_python; result = cfd_python.run_simulation(5, 5, 3); print(f'Computed {len(result)} points')"
```

---

## Release Process

Version is automatically determined from git tags via setuptools-scm (configured in `pyproject.toml`). Do not manually update version numbers.

1. Ensure all changes are committed and pushed
2. Create and push a release tag:

   ```bash
   git tag v0.3.0
   git push origin v0.3.0
   ```

3. GitHub Actions automatically builds wheels and publishes to PyPI

The version string is derived from the git tag (e.g., tag `v0.3.0` → version `0.3.0`).

---

## Troubleshooting

### Build Fails: "CFD library not found"

Ensure the C library is built first:
```bash
cd ../cfd
cmake -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
cmake --build build --config Release
```

### Import Error: Missing Symbols

This usually means static linking wasn't enabled. Check that:

- `CFD_STATIC_LINK=ON` is set in CMake
- The static library (`.a` or `_static.lib`) exists in the build directory

### New Solver Not Appearing

1. Verify the solver is registered in the C library's solver registry
2. Rebuild the C library
3. Rebuild the Python extension
4. Check with `cfd_python.list_solvers()`
