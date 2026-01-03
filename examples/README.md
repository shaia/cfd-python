# CFD Python Examples

This directory contains example scripts demonstrating how to use the CFD Python library.

## Examples Overview

### Basic Usage

| Example | Description |
|---------|-------------|
| [basic_example.py](basic_example.py) | Fundamental usage of all main functions |
| [solver_discovery.py](solver_discovery.py) | Discovering and using different solvers |
| [error_handling.py](error_handling.py) | Error handling API with exceptions |

### Simulation Examples

| Example | Description |
|---------|-------------|
| [lid_driven_cavity.py](lid_driven_cavity.py) | Classic CFD benchmark problem |
| [lid_driven_cavity_advanced.py](lid_driven_cavity_advanced.py) | Advanced cavity simulation with time stepping |
| [channel_flow.py](channel_flow.py) | Channel flow with inlet/outlet BCs |
| [parameter_study.py](parameter_study.py) | Running parameter studies and comparisons |

### Boundary Conditions

| Example | Description |
|---------|-------------|
| [boundary_conditions.py](boundary_conditions.py) | Full boundary conditions API demo |

### Output and Visualization

| Example | Description |
|---------|-------------|
| [output_formats.py](output_formats.py) | Exporting to VTK and CSV formats |
| [vtk_output.py](vtk_output.py) | VTK output for ParaView visualization |
| [visualization_numpy.py](visualization_numpy.py) | NumPy analysis of simulation results |
| [visualization_matplotlib.py](visualization_matplotlib.py) | Matplotlib plots (contours, vectors, streamlines, 3D Rankine vortex) |

### Derived Fields

| Example | Description |
|---------|-------------|
| [derived_fields.py](derived_fields.py) | Computing derived quantities and statistics |

## Running Examples

Make sure the package is installed first:

```bash
# Install in development mode
pip install -e .
```

Then run any example:

```bash
cd examples
python basic_example.py
python visualization_matplotlib.py
```

## Output Files

All examples write output files to the `output/` subdirectory. This directory is automatically created when running examples and is excluded from git.

Output file types:
- `.vtk` files - Open with ParaView or VisIt for 3D visualization
- `.csv` files - Open with Excel, Python pandas, or any text editor
- `.png` files - Matplotlib visualizations

## Requirements

- `cfd_python` package (this library)
- `numpy` (included as dependency)

Optional for visualization:
- `matplotlib` for plotting (visualization_matplotlib.py)
- ParaView or VisIt for VTK file visualization
