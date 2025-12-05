# CFD Python

Python bindings for high-performance CFD simulation library using CPython C-API with stable ABI (abi3).

## Features

- **High Performance**: Direct bindings to optimized C library
- **Stable ABI**: Compatible across Python 3.9+ versions
- **Static Linking**: Self-contained wheels with no external dependencies
- **Dynamic Solver Discovery**: New solvers automatically available
- **Multiple Output Formats**: VTK and CSV export support

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
cfd_python.OUTPUT_PRESSURE        # Pressure field (VTK)
cfd_python.OUTPUT_VELOCITY        # Velocity field (VTK)
cfd_python.OUTPUT_FULL_FIELD      # Complete flow field (VTK)
cfd_python.OUTPUT_CSV_TIMESERIES  # Time series (CSV)
cfd_python.OUTPUT_CSV_CENTERLINE  # Centerline profile (CSV)
cfd_python.OUTPUT_CSV_STATISTICS  # Global statistics (CSV)
```

## Requirements

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

For building from source:

- C compiler (MSVC on Windows, GCC/Clang on Unix)
- CMake 3.15+

## License

MIT License
