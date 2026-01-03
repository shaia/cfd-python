# CFD Python

Python bindings for high-performance CFD simulation library using CPython C-API with stable ABI (abi3).

## Features

- **High Performance**: Direct bindings to optimized C library with SIMD (AVX2/NEON) and OpenMP support
- **Stable ABI**: Compatible across Python 3.9+ versions
- **Multiple Backends**: Scalar, SIMD, OpenMP, and CUDA (GPU) backends with runtime detection
- **Boundary Conditions**: Full BC support (Neumann, Dirichlet, no-slip, inlet, outlet)
- **Dynamic Solver Discovery**: New solvers automatically available
- **Multiple Output Formats**: VTK and CSV export support
- **Error Handling**: Rich exception hierarchy with detailed error messages

## Installation

### Installing uv (optional but recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package manager. Install it with:

```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

### From PyPI

Using uv (recommended):

```bash
uv pip install cfd-python
```

Or with pip:

```bash
pip install cfd-python
```

### From Source

The Python package requires the C CFD library to be built first. By default, it expects the library at `../cfd` relative to the cfd-python directory. You can override this by setting the `CFD_ROOT` environment variable.

1. Build the C CFD library (static):

   ```bash
   cd ../cfd
   cmake -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
   cmake --build build --config Release
   ```

2. Install the Python package:

   ```bash
   cd ../cfd-python
   pip install .
   ```

   Or with [uv](https://docs.astral.sh/uv/) for faster installs:

   ```bash
   uv pip install .
   ```

   With a custom library location:

   ```bash
   CFD_ROOT=/path/to/cfd pip install .
   ```

### For Development

We use [uv](https://docs.astral.sh/uv/) for fast dependency management:

```bash
# Create virtual environment
uv venv

# Activate it
source .venv/bin/activate      # Linux/macOS
source .venv/Scripts/activate  # Windows (Git Bash)
.venv\Scripts\activate         # Windows (cmd)

# Install with dev dependencies
uv pip install -e ".[test,dev]"
```

Alternatively, using pip:

```bash
pip install -e ".[test,dev]"
```

## Quick Start

```python
import cfd_python

# List available solvers
print(cfd_python.list_solvers())
# ['explicit_euler', 'explicit_euler_optimized', 'projection', ...]

# Run a simple simulation
velocity_magnitude = cfd_python.run_simulation(50, 50, steps=100)
print(f"Computed {len(velocity_magnitude)} velocity values")

# Create a grid
grid = cfd_python.create_grid(100, 100, 0.0, 1.0, 0.0, 1.0)
print(f"Grid: {grid['nx']}x{grid['ny']}")

# Get default solver parameters
params = cfd_python.get_default_solver_params()
print(f"Default dt: {params['dt']}")
```

## API Reference

### Simulation Functions

#### `run_simulation(nx, ny, steps=100, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0, solver_type=None, output_file=None)`

Run a complete simulation with default parameters.

**Parameters:**

- `nx`, `ny`: Grid dimensions
- `steps`: Number of time steps (default: 100)
- `xmin`, `xmax`, `ymin`, `ymax`: Domain bounds (optional)
- `solver_type`: Solver name string (optional, uses library default)
- `output_file`: VTK output file path (optional)

**Returns:** List of velocity magnitude values

#### `run_simulation_with_params(nx, ny, xmin, xmax, ymin, ymax, steps=1, dt=0.001, cfl=0.2, solver_type=None, output_file=None)`

Run simulation with custom parameters and solver selection.

**Parameters:**

- `nx`, `ny`: Grid dimensions
- `xmin`, `xmax`, `ymin`, `ymax`: Domain bounds
- `steps`: Number of time steps (default: 1)
- `dt`: Time step size (default: 0.001)
- `cfl`: CFL number (default: 0.2)
- `solver_type`: Solver name string (optional, uses library default)
- `output_file`: VTK output file path (optional)

**Returns:** Dictionary with `velocity_magnitude`, `nx`, `ny`, `steps`, `solver_name`, `solver_description`, and `stats`

#### `create_grid(nx, ny, xmin, xmax, ymin, ymax)`

Create a computational grid.

**Parameters:**

- `nx`, `ny`: Grid dimensions
- `xmin`, `xmax`, `ymin`, `ymax`: Domain bounds

**Returns:** Dictionary with `nx`, `ny`, `xmin`, `xmax`, `ymin`, `ymax`, `x_coords`, `y_coords`

#### `create_grid_stretched(nx, ny, xmin, xmax, ymin, ymax, beta)`

Create a grid with non-uniform (stretched) spacing.

**Parameters:**

- `nx`, `ny`: Grid dimensions
- `xmin`, `xmax`, `ymin`, `ymax`: Domain bounds
- `beta`: Stretching parameter (higher = more clustering)

**Returns:** Dictionary with grid info including `x_coords`, `y_coords`

> **Note:** The stretched grid implementation has a known bug - see ROADMAP.md for details.

#### `get_default_solver_params()`

Get default solver parameters.

**Returns:** Dictionary with keys: `dt`, `cfl`, `gamma`, `mu`, `k`, `max_iter`, `tolerance`

### Solver Discovery

#### `list_solvers()`

Get list of all available solver names.

**Returns:** List of solver name strings

#### `has_solver(name)`

Check if a solver is available.

**Returns:** Boolean

#### `get_solver_info(name)`

Get information about a solver.

**Returns:** Dictionary with `name`, `description`, `version`, `capabilities`

### Dynamic Solver Constants

Solver constants are automatically generated from the registry:

```python
cfd_python.SOLVER_EXPLICIT_EULER           # 'explicit_euler'
cfd_python.SOLVER_EXPLICIT_EULER_OPTIMIZED # 'explicit_euler_optimized'
cfd_python.SOLVER_PROJECTION               # 'projection'
# ... more solvers as registered in C library
```

### Backend Availability (v0.1.6+)

Query and select compute backends at runtime:

```python
import cfd_python

# Check available backends
print(cfd_python.get_available_backends())
# ['Scalar', 'SIMD', 'OpenMP']  # CUDA if GPU available

# Check specific backend
if cfd_python.backend_is_available(cfd_python.BACKEND_SIMD):
    print("SIMD backend available!")

# Get backend name
print(cfd_python.backend_get_name(cfd_python.BACKEND_OMP))  # 'OpenMP'

# List solvers for a backend
omp_solvers = cfd_python.list_solvers_by_backend(cfd_python.BACKEND_OMP)
print(f"OpenMP solvers: {omp_solvers}")
```

**Backend Constants:**

- `BACKEND_SCALAR`: Basic scalar CPU implementation
- `BACKEND_SIMD`: SIMD-optimized (AVX2/NEON)
- `BACKEND_OMP`: OpenMP parallelized
- `BACKEND_CUDA`: CUDA GPU acceleration

### Boundary Conditions

Apply various boundary conditions to flow fields:

```python
import cfd_python

# Create velocity field (as flat lists)
nx, ny = 50, 50
u = [0.0] * (nx * ny)
v = [0.0] * (nx * ny)

# Apply uniform inlet on left edge
cfd_python.bc_apply_inlet_uniform(
    u, v, nx, ny,
    u_inlet=1.0, v_inlet=0.0,
    edge=cfd_python.BC_EDGE_LEFT
)

# Apply zero-gradient outlet on right edge
cfd_python.bc_apply_outlet_velocity(u, v, nx, ny, cfd_python.BC_EDGE_RIGHT)

# Apply no-slip walls on top and bottom
cfd_python.bc_apply_noslip(u, v, nx, ny)

# Check/set BC backend
print(f"BC Backend: {cfd_python.bc_get_backend_name()}")
if cfd_python.bc_backend_available(cfd_python.BC_BACKEND_OMP):
    cfd_python.bc_set_backend(cfd_python.BC_BACKEND_OMP)
```

**BC Type Constants:**

- `BC_TYPE_PERIODIC`: Periodic boundaries
- `BC_TYPE_NEUMANN`: Zero-gradient boundaries
- `BC_TYPE_DIRICHLET`: Fixed value boundaries
- `BC_TYPE_NOSLIP`: No-slip wall (zero velocity)
- `BC_TYPE_INLET`: Inlet velocity specification
- `BC_TYPE_OUTLET`: Outlet conditions

**BC Edge Constants:**

- `BC_EDGE_LEFT`, `BC_EDGE_RIGHT`, `BC_EDGE_BOTTOM`, `BC_EDGE_TOP`

**BC Backend Constants:**

- `BC_BACKEND_AUTO`: Auto-select best available
- `BC_BACKEND_SCALAR`: Single-threaded scalar
- `BC_BACKEND_OMP`: OpenMP parallel
- `BC_BACKEND_SIMD`: SIMD + OpenMP (AVX2/NEON)
- `BC_BACKEND_CUDA`: GPU acceleration

**BC Functions:**

- `bc_apply_scalar(field, nx, ny, bc_type)`: Apply BC to scalar field
- `bc_apply_velocity(u, v, nx, ny, bc_type)`: Apply BC to velocity fields
- `bc_apply_dirichlet(field, nx, ny, left, right, bottom, top)`: Fixed values
- `bc_apply_noslip(u, v, nx, ny)`: Zero velocity at walls
- `bc_apply_inlet_uniform(u, v, nx, ny, u_inlet, v_inlet, edge)`: Uniform inlet
- `bc_apply_inlet_parabolic(u, v, nx, ny, max_velocity, edge)`: Parabolic inlet
- `bc_apply_outlet_scalar(field, nx, ny, edge)`: Zero-gradient outlet
- `bc_apply_outlet_velocity(u, v, nx, ny, edge)`: Zero-gradient outlet

### Derived Fields & Statistics

Compute derived quantities from flow fields:

```python
import cfd_python

# Compute velocity magnitude
u = [1.0] * 100
v = [0.5] * 100
vel_mag = cfd_python.compute_velocity_magnitude(u, v, 10, 10)

# Calculate field statistics
stats = cfd_python.calculate_field_stats(vel_mag)
print(f"Min: {stats['min']}, Max: {stats['max']}, Avg: {stats['avg']}")

# Comprehensive flow statistics
p = [0.0] * 100  # pressure field
flow_stats = cfd_python.compute_flow_statistics(u, v, p, 10, 10)
print(f"Max velocity: {flow_stats['velocity_magnitude']['max']}")
```

### CPU Features Detection

Detect SIMD capabilities at runtime:

```python
import cfd_python

# Check SIMD architecture
arch = cfd_python.get_simd_arch()
name = cfd_python.get_simd_name()  # 'avx2', 'neon', or 'none'

# Check specific capabilities
if cfd_python.has_avx2():
    print("AVX2 available!")
elif cfd_python.has_neon():
    print("ARM NEON available!")

# General SIMD check
if cfd_python.has_simd():
    print(f"SIMD enabled: {name}")
```

**SIMD Constants:**

- `SIMD_NONE`: No SIMD support
- `SIMD_AVX2`: x86-64 AVX2
- `SIMD_NEON`: ARM NEON

### Error Handling

Handle errors with Python exceptions:

```python
import cfd_python
from cfd_python import (
    CFDError,
    CFDMemoryError,
    CFDInvalidError,
    CFDDivergedError,
    raise_for_status,
)

# Check status codes
status = cfd_python.get_last_status()
if status != cfd_python.CFD_SUCCESS:
    error_msg = cfd_python.get_last_error()
    print(f"Error: {error_msg}")

# Use raise_for_status helper
try:
    raise_for_status(status, context="simulation step")
except CFDDivergedError as e:
    print(f"Solver diverged: {e}")
except CFDInvalidError as e:
    print(f"Invalid parameter: {e}")
except CFDError as e:
    print(f"CFD error: {e}")

# Clear error state
cfd_python.clear_error()
```

**Error Constants:**

- `CFD_SUCCESS`: Operation successful (0)
- `CFD_ERROR`: Generic error (-1)
- `CFD_ERROR_NOMEM`: Out of memory (-2)
- `CFD_ERROR_INVALID`: Invalid argument (-3)
- `CFD_ERROR_IO`: File I/O error (-4)
- `CFD_ERROR_UNSUPPORTED`: Operation not supported (-5)
- `CFD_ERROR_DIVERGED`: Solver diverged (-6)
- `CFD_ERROR_MAX_ITER`: Max iterations reached (-7)

**Exception Classes:**

- `CFDError`: Base exception class
- `CFDMemoryError(CFDError, MemoryError)`: Memory allocation failed
- `CFDInvalidError(CFDError, ValueError)`: Invalid argument
- `CFDIOError(CFDError, IOError)`: File I/O error
- `CFDUnsupportedError(CFDError, NotImplementedError)`: Unsupported operation
- `CFDDivergedError(CFDError)`: Solver diverged
- `CFDMaxIterError(CFDError)`: Max iterations reached

### Output Functions

#### `set_output_dir(directory)`

Set the output directory for VTK/CSV files.

#### `write_vtk_scalar(filename, field_name, data, nx, ny, xmin, xmax, ymin, ymax)`

Write scalar field to VTK file.

#### `write_vtk_vector(filename, field_name, u_data, v_data, nx, ny, xmin, xmax, ymin, ymax)`

Write vector field to VTK file.

#### `write_csv_timeseries(filename, step, time, u_data, v_data, p_data, nx, ny, dt, iterations, create_new=False)`

Write simulation timeseries data to CSV file.

**Parameters:**

- `filename`: Output file path
- `step`: Time step number
- `time`: Simulation time
- `u_data`, `v_data`, `p_data`: Flow field data as lists (size nx*ny)
- `nx`, `ny`: Grid dimensions
- `dt`: Time step size
- `iterations`: Number of solver iterations
- `create_new`: If True, create new file; if False, append

### Output Type Constants

```python
cfd_python.OUTPUT_VELOCITY_MAGNITUDE  # Velocity magnitude scalar (VTK)
cfd_python.OUTPUT_VELOCITY            # Velocity vector field (VTK)
cfd_python.OUTPUT_FULL_FIELD          # Complete flow field (VTK)
cfd_python.OUTPUT_CSV_TIMESERIES      # Time series (CSV)
cfd_python.OUTPUT_CSV_CENTERLINE      # Centerline profile (CSV)
cfd_python.OUTPUT_CSV_STATISTICS      # Global statistics (CSV)
```

## Migration from v0.1.0

If you're upgrading from an older version, note these changes:

### API Changes

1. **Type names changed** (internal, transparent to Python users)
2. **Error handling improved**: Use `get_last_error()`, `get_last_status()`, `clear_error()`
3. **New solver backends**: SIMD, OpenMP, CUDA available via `backend_is_available()`

### New Features in v0.1.6

- **Boundary conditions**: Full BC API with inlet/outlet support
- **Backend selection**: Query and select compute backends at runtime
- **Derived fields**: `compute_velocity_magnitude()`, `compute_flow_statistics()`
- **Error handling**: Python exception classes with `raise_for_status()`
- **CPU detection**: `has_avx2()`, `has_neon()`, `has_simd()`

See [MIGRATION_PLAN.md](MIGRATION_PLAN.md) for detailed migration information.

## Requirements

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

For building from source:

- C compiler (MSVC on Windows, GCC/Clang on Unix)
- CMake 3.15+

## License

MIT License
