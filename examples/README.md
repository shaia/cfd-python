# CFD Python Examples

This directory contains example scripts demonstrating how to use the CFD Python library.

## Examples

### Basic Usage

| Example | Description |
|---------|-------------|
| [basic_example.py](basic_example.py) | Fundamental usage of all main functions |
| [solver_discovery.py](solver_discovery.py) | Discovering and using different solvers |

### Output and Visualization

| Example | Description |
|---------|-------------|
| [output_formats.py](output_formats.py) | Exporting to VTK and CSV formats |
| [visualization_numpy.py](visualization_numpy.py) | NumPy analysis of simulation results |

### Advanced Usage

| Example | Description |
|---------|-------------|
| [parameter_study.py](parameter_study.py) | Running parameter studies and comparisons |
| [lid_driven_cavity.py](lid_driven_cavity.py) | Classic CFD benchmark problem |

## Running Examples

Make sure the package is installed first:

```bash
# Install in development mode
pip install -e .

# Or using build.py
python build.py develop
```

Then run any example:

```bash
cd examples
python basic_example.py
python solver_discovery.py
python output_formats.py
```

## Output Files

Examples may generate output files:

- `.vtk` files - Open with ParaView or VisIt for visualization
- `.csv` files - Open with Excel, Python pandas, or any text editor

## Requirements

- `cfd_python` package (this library)
- `numpy` (included as dependency)

Optional for visualization:
- `matplotlib` for plotting
- ParaView or VisIt for VTK visualization
