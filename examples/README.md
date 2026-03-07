# CFD Python Examples

This directory contains example scripts demonstrating how to use the CFD Python library.

## Examples Overview

### Basic Usage

| Example | Description |
|---------|-------------|
| [basic_example.py](basic_example.py) | Fundamental usage of all main functions |
| [solver_discovery.py](solver_discovery.py) | Discovering and using different solvers |
| [solver_comparison.py](solver_comparison.py) | Comparing different solver implementations |
| [backend_detection.py](backend_detection.py) | Detecting SIMD/OpenMP/CUDA backend availability |
| [error_handling.py](error_handling.py) | Error handling API with exceptions |

### v0.2.0 Features

| Example | Description |
|---------|-------------|
| [library_lifecycle.py](library_lifecycle.py) | Library init/finalize, version queries (v0.2.0) |
| [poisson_solver.py](poisson_solver.py) | Poisson solver methods, backends, and presets (v0.2.0) |
| [gpu_management.py](gpu_management.py) | GPU device detection, selection, and configuration (v0.2.0) |
| [logging_example.py](logging_example.py) | Python logging callbacks for C library messages (v0.2.0) |
| [grid_3d.py](grid_3d.py) | 3D grid creation and VTK output (v0.2.0) |

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

### Physics Benchmarks

| Example | Description |
|---------|-------------|
| [heat_conduction.py](heat_conduction.py) | Steady-state heat conduction with Dirichlet BCs and Jacobi iteration |
| [taylor_green_vortex.py](taylor_green_vortex.py) | Taylor-Green vortex decay with analytical validation |
| [backward_facing_step.py](backward_facing_step.py) | Backward-facing step with recirculation and stretched grid |
| [duct_flow_3d.py](duct_flow_3d.py) | 3D square duct flow with cross-section analysis |
| [grid_convergence.py](grid_convergence.py) | Formal grid convergence study with L2 error and GCI |
| [poisson_comparison.py](poisson_comparison.py) | Poisson solver method and backend performance comparison |

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
