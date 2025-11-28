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

The build system uses `CFD_STATIC_LINK` to control linking:

```cmake
option(CFD_STATIC_LINK "Statically link the CFD library" ON)

if(CFD_STATIC_LINK)
    # Windows: look for cfd_library_static.lib
    # Unix: look for libcfd_library.a
    find_library(CFD_LIBRARY
        NAMES cfd_library_static cfd_library libcfd_library.a
        PATHS ${CFD_LIBRARY_DIR}
        NO_DEFAULT_PATH
    )
endif()
```

### pyproject.toml

Static linking is enabled in the build configuration:

```toml
[tool.scikit-build.cmake.define]
CMAKE_BUILD_TYPE = "Release"
CFD_STATIC_LINK = "ON"

[tool.cibuildwheel]
environment = { CMAKE_BUILD_TYPE = "Release", CFD_STATIC_LINK = "ON" }
```

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

### Build Wheels with cibuildwheel

```bash
pip install cibuildwheel
python -m cibuildwheel --output-dir wheelhouse
```

This creates wheels for Python 3.8-3.12 on all platforms.

### Platform-Specific Build Steps

The `pyproject.toml` configures platform-specific build steps:

**Windows:**
```toml
[tool.cibuildwheel.windows]
before-build = [
    "cd ../cfd && cmake -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF",
    "cd ../cfd && cmake --build build --config Release",
]
```

**macOS:**
```toml
[tool.cibuildwheel.macos]
before-build = [
    "cd ../cfd && cmake -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF",
    "cd ../cfd && cmake --build build --config Release",
]
repair-wheel-command = "delocate-wheel --require-archs {delocate_archs} -w {dest_dir} {wheel}"
```

**Linux:**
```toml
[tool.cibuildwheel.linux]
before-all = [
    "yum install -y cmake3 gcc-c++ || apt-get update && apt-get install -y cmake g++",
]
before-build = [
    "cd ../cfd && cmake -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF",
    "cd ../cfd && cmake --build build --config Release",
]
repair-wheel-command = "auditwheel repair -w {dest_dir} {wheel}"
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
name: Build and Test

on: [push, pull_request]

jobs:
  build_wheels:
    name: Build wheels on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]

    steps:
      - uses: actions/checkout@v4
        with:
          submodules: true
      - uses: pypa/cibuildwheel@v2.16.2
      - uses: actions/upload-artifact@v3
        with:
          path: ./wheelhouse/*.whl

  upload_pypi:
    needs: [build_wheels]
    runs-on: ubuntu-latest
    if: github.event_name == 'release'
    steps:
      - uses: actions/download-artifact@v3
      - uses: pypa/gh-action-pypi-publish@v1.8.10
```

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

1. Update version in `cfd_python/__init__.py`
2. Push to GitHub (triggers automated builds)
3. Create release tag:

   ```bash
   git tag v0.3.0
   git push origin v0.3.0
   ```

4. GitHub Actions automatically publishes to PyPI

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
