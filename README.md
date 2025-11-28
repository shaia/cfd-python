# cfd-python

High-performance CFD simulation library with Python bindings.

## Installation

```bash
pip install cfd-python
```

## Usage

```python
import cfd_python

# List available solvers
solvers = cfd_python.list_solvers()
print(f"Available solvers: {solvers}")

# Run a basic simulation
result = cfd_python.run_simulation(nx=32, ny=32, steps=100)
print(f"Computed {len(result)} points")

# Create a grid
grid = cfd_python.create_grid(nx=10, ny=10, xmin=0.0, xmax=1.0, ymin=0.0, ymax=1.0)
print(f"Grid dimensions: {grid['nx']}x{grid['ny']}")
```

## Building from source

Requires the CFD C library to be built first:

```bash
# Build the CFD library (in ../cfd directory)
cd ../cfd
cmake -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF
cmake --build build --config Release

# Build and install cfd-python
cd ../cfd-python
pip install -e .
```

## License

MIT
