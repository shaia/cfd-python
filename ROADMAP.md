# CFD-Python Future Roadmap

This document outlines planned enhancements and new features for cfd-python after the v0.1.6 migration is complete.

**Last Updated:** 2026-01-02
**Current Version:** 0.1.6 (migration in progress)
**Target Version:** 0.2.0+

---

## Overview

With the v0.1.6 migration completing core functionality (boundary conditions, error handling, backend availability, CPU features), the focus shifts to improving the Python API ergonomics, adding type safety, and providing higher-level abstractions.

---

## Phase 8: Type Stubs & IDE Support

**Priority:** P1 - High impact for developer experience
**Estimated Effort:** 2-3 days

### Goals

- Enable IDE autocompletion for all C extension functions
- Provide type checking with mypy/pyright
- Document function signatures formally

### Tasks

- [ ] **8.1 Create `cfd_python.pyi` stub file**
  ```python
  # Example stub content
  from typing import Dict, List, Optional, Union

  # Constants
  SIMD_NONE: int
  SIMD_AVX2: int
  SIMD_NEON: int

  BACKEND_SCALAR: int
  BACKEND_SIMD: int
  BACKEND_OMP: int
  BACKEND_CUDA: int

  # Functions
  def create_grid(
      nx: int,
      ny: int,
      xmin: float,
      xmax: float,
      ymin: float,
      ymax: float,
  ) -> Dict[str, Union[int, float, List[float]]]: ...

  def run_simulation(
      nx: int,
      ny: int,
      *,
      steps: int = ...,
      solver_type: str = ...,
      xmin: float = ...,
      xmax: float = ...,
      ymin: float = ...,
      ymax: float = ...,
      output_file: Optional[str] = ...,
  ) -> List[float]: ...
  ```

- [ ] **8.2 Add `py.typed` marker file**
  - Create empty `cfd_python/py.typed` for PEP 561 compliance

- [ ] **8.3 Update `pyproject.toml`**
  - Add stub files to package data
  - Configure mypy/pyright settings

- [ ] **8.4 Add type checking to CI**
  - Run mypy on tests to verify stubs are correct

### Success Criteria

- IDE shows function signatures and return types
- `mypy tests/` passes without errors
- Stubs cover all exported functions and constants

---

## Phase 9: IntEnum Constants

**Priority:** P2 - Improved API ergonomics
**Estimated Effort:** 1-2 days

### Goals

- Replace bare integer constants with IntEnum classes
- Better repr/str output for debugging
- IDE support for constant groups

### Tasks

- [ ] **9.1 Create enum classes in `_enums.py`**
  ```python
  from enum import IntEnum

  class SIMDArch(IntEnum):
      """SIMD architecture detected on the system."""
      NONE = 0
      AVX2 = 1
      NEON = 2

  class Backend(IntEnum):
      """Solver backend types."""
      SCALAR = 0
      SIMD = 1
      OMP = 2
      CUDA = 3

  class BCType(IntEnum):
      """Boundary condition types."""
      PERIODIC = 0
      NEUMANN = 1
      DIRICHLET = 2
      NOSLIP = 3
      INLET = 4
      OUTLET = 5

  class BCEdge(IntEnum):
      """Boundary edges."""
      LEFT = 0
      RIGHT = 1
      BOTTOM = 2
      TOP = 3

  class BCBackend(IntEnum):
      """Boundary condition backends."""
      AUTO = 0
      SCALAR = 1
      OMP = 2
      SIMD = 3
      CUDA = 4

  class OutputType(IntEnum):
      """Output file types."""
      VELOCITY = 0
      VELOCITY_MAGNITUDE = 1
      FULL_FIELD = 2
      CSV_TIMESERIES = 3
      CSV_CENTERLINE = 4
      CSV_STATISTICS = 5

  class StatusCode(IntEnum):
      """CFD operation status codes."""
      SUCCESS = 0
      ERROR = -1
      ERROR_NOMEM = -2
      ERROR_INVALID = -3
      ERROR_IO = -4
      ERROR_UNSUPPORTED = -5
      ERROR_DIVERGED = -6
      ERROR_MAX_ITER = -7
  ```

- [ ] **9.2 Export enums alongside bare constants**
  - Maintain backward compatibility with `SIMD_NONE`, `BACKEND_SCALAR`, etc.
  - Add enum classes to `__all__`

- [ ] **9.3 Update documentation**
  - Show enum usage in docstrings
  - Add migration notes for users preferring enums

- [ ] **9.4 Add tests for enum classes**

### Success Criteria

- Both `cfd_python.SIMD_AVX2` and `cfd_python.SIMDArch.AVX2` work
- `str(SIMDArch.AVX2)` returns `"SIMDArch.AVX2"`
- Enums work with existing functions that expect int constants

---

## Phase 10: High-Level Pythonic Wrappers

**Priority:** P2 - Developer experience improvement
**Estimated Effort:** 3-5 days

### Goals

- Provide object-oriented API alongside functional API
- Reduce boilerplate for common operations
- Enable method chaining and fluent interfaces

### Tasks

- [ ] **10.1 Create `Grid` class**
  ```python
  class Grid:
      """High-level grid object with coordinate access."""

      def __init__(self, nx: int, ny: int,
                   xmin: float = 0.0, xmax: float = 1.0,
                   ymin: float = 0.0, ymax: float = 1.0,
                   stretching: Optional[float] = None):
          if stretching is not None:
              self._data = create_grid_stretched(nx, ny, xmin, xmax, ymin, ymax, stretching)
          else:
              self._data = create_grid(nx, ny, xmin, xmax, ymin, ymax)

      @property
      def nx(self) -> int:
          return self._data["nx"]

      @property
      def ny(self) -> int:
          return self._data["ny"]

      @property
      def x(self) -> List[float]:
          return self._data.get("x", self._data.get("x_coords", []))

      @property
      def y(self) -> List[float]:
          return self._data.get("y", self._data.get("y_coords", []))

      @property
      def shape(self) -> tuple[int, int]:
          return (self.nx, self.ny)

      @property
      def bounds(self) -> tuple[float, float, float, float]:
          return (self._data["xmin"], self._data["xmax"],
                  self._data["ymin"], self._data["ymax"])
  ```

- [ ] **10.2 Create `BoundaryConditions` builder**
  ```python
  class BoundaryConditions:
      """Fluent builder for boundary conditions."""

      def __init__(self, u: List[float], v: List[float], nx: int, ny: int):
          self.u = u
          self.v = v
          self.nx = nx
          self.ny = ny

      def noslip_walls(self) -> "BoundaryConditions":
          """Apply no-slip condition to all walls."""
          bc_apply_noslip(self.u, self.v, self.nx, self.ny)
          return self

      def inlet_uniform(self, edge: BCEdge, u: float, v: float = 0.0) -> "BoundaryConditions":
          """Apply uniform inlet velocity."""
          bc_apply_inlet_uniform(self.u, self.v, self.nx, self.ny, u, v, int(edge))
          return self

      def inlet_parabolic(self, edge: BCEdge, max_velocity: float) -> "BoundaryConditions":
          """Apply parabolic inlet profile."""
          bc_apply_inlet_parabolic(self.u, self.v, self.nx, self.ny, max_velocity, int(edge))
          return self

      def outlet(self, edge: BCEdge) -> "BoundaryConditions":
          """Apply zero-gradient outlet."""
          bc_apply_outlet_velocity(self.u, self.v, self.nx, self.ny, int(edge))
          return self

      # Context manager support
      def __enter__(self) -> "BoundaryConditions":
          return self

      def __exit__(self, *args) -> None:
          pass

  # Usage:
  # bc = BoundaryConditions(u, v, nx, ny)
  # bc.noslip_walls().inlet_uniform(BCEdge.LEFT, u=1.0).outlet(BCEdge.RIGHT)
  ```

- [ ] **10.3 Create `Simulation` class**
  ```python
  class Simulation:
      """High-level simulation runner."""

      def __init__(self, grid: Grid, solver: str = "explicit_euler"):
          self.grid = grid
          self.solver = solver
          self._params = get_default_solver_params()
          self._result = None

      def set_params(self, **kwargs) -> "Simulation":
          """Set solver parameters."""
          self._params.update(kwargs)
          return self

      def run(self, steps: int, output_file: Optional[str] = None) -> "SimulationResult":
          """Run the simulation."""
          result = run_simulation_with_params(
              self.grid.nx, self.grid.ny,
              *self.grid.bounds,
              steps=steps,
              solver_type=self.solver,
              output_file=output_file,
              **self._params
          )
          self._result = SimulationResult(result)
          return self._result

  class SimulationResult:
      """Container for simulation results with statistics."""

      def __init__(self, data: dict):
          self._data = data

      @property
      def velocity_magnitude(self) -> List[float]:
          return self._data["velocity_magnitude"]

      @property
      def stats(self) -> dict:
          return self._data["stats"]

      def compute_statistics(self, u: List[float], v: List[float], p: List[float]) -> dict:
          return compute_flow_statistics(u, v, p, self._data["nx"], self._data["ny"])
  ```

- [ ] **10.4 Create `Field` class for data manipulation**
  ```python
  class Field:
      """Scalar field with statistics and operations."""

      def __init__(self, data: List[float], nx: int, ny: int):
          self.data = data
          self.nx = nx
          self.ny = ny

      @property
      def shape(self) -> tuple[int, int]:
          return (self.nx, self.ny)

      @property
      def stats(self) -> dict:
          return calculate_field_stats(self.data)

      @property
      def min(self) -> float:
          return self.stats["min"]

      @property
      def max(self) -> float:
          return self.stats["max"]

      @property
      def mean(self) -> float:
          return self.stats["avg"]

      def to_vtk(self, filename: str, name: str = "field") -> None:
          write_vtk_scalar(filename, name, self.data, self.nx, self.ny,
                          0.0, 1.0, 0.0, 1.0)
  ```

- [ ] **10.5 Add tests for high-level API**

- [ ] **10.6 Update documentation with examples**

### Success Criteria

- Users can choose between low-level functions and high-level classes
- Method chaining works fluently
- All high-level classes have comprehensive tests

---

## Phase 11: NumPy Integration

**Priority:** P2 - Important for scientific workflows
**Estimated Effort:** 2-3 days

### Goals

- Accept and return NumPy arrays
- Zero-copy data transfer where possible
- Integration with NumPy ecosystem

### Tasks

- [ ] **11.1 Add NumPy array support to C extension**
  - Use `PyArray_*` API for array handling
  - Support both list and ndarray inputs

- [ ] **11.2 Create array conversion utilities**
  ```python
  def to_numpy(data: List[float], shape: tuple[int, int]) -> np.ndarray:
      """Convert flat list to 2D NumPy array."""
      return np.array(data).reshape(shape)

  def from_numpy(arr: np.ndarray) -> List[float]:
      """Convert NumPy array to flat list."""
      return arr.flatten().tolist()
  ```

- [ ] **11.3 Add `as_numpy` option to functions**
  ```python
  def run_simulation(..., as_numpy: bool = False) -> Union[List[float], np.ndarray]:
      result = _run_simulation_impl(...)
      if as_numpy:
          return np.array(result).reshape((ny, nx))
      return result
  ```

- [ ] **11.4 Support array protocol in Field class**
  ```python
  class Field:
      def __array__(self) -> np.ndarray:
          return np.array(self.data).reshape(self.shape)
  ```

- [ ] **11.5 Add tests with NumPy arrays**

### Success Criteria

- Functions accept both lists and NumPy arrays
- NumPy arrays can be returned directly
- Field objects work with NumPy functions via `__array__`

---

## Phase 12: Integration with cfd-visualization

**Priority:** P2 - Leverage existing visualization library
**Estimated Effort:** 1 day

### Goals

- Enable optional dependency on cfd-visualization
- Reference cfd-visualization for all visualization needs

### Note

Visualization features are developed in the separate `cfd-visualization` project.
See [cfd-visualization ROADMAP](../cfd-visualization/ROADMAP.md) for visualization enhancements.

### Tasks

- [ ] **12.1 Add optional dependency**
  ```toml
  [project.optional-dependencies]
  viz = ["cfd-visualization>=0.2.0"]
  ```

- [ ] **12.2 Document integration in examples**
  - Show how to use `cfd_viz.from_cfd_python()` conversion
  - Reference cfd-visualization documentation

### Success Criteria

- `pip install cfd-python[viz]` installs cfd-visualization
- Documentation points users to cfd-visualization for visualization

---

## Phase 13: Performance Profiling API

**Priority:** P3 - Useful for optimization
**Estimated Effort:** 1-2 days

### Goals

- Expose timing information from C library
- Help users identify bottlenecks
- Support benchmarking workflows

### Tasks

- [ ] **13.1 Add timing to simulation results**
  ```python
  result = run_simulation_with_params(...)
  print(result["timing"])
  # {'total_ms': 150.2, 'solver_ms': 120.5, 'bc_ms': 25.3, 'io_ms': 4.4}
  ```

- [ ] **13.2 Create benchmarking utilities**
  ```python
  from cfd_python.benchmark import benchmark_solver

  results = benchmark_solver(
      solver="projection",
      grid_sizes=[(32, 32), (64, 64), (128, 128)],
      steps=100,
      repeat=3
  )
  # Returns DataFrame with timing statistics
  ```

- [ ] **13.3 Add backend comparison utility**
  ```python
  from cfd_python.benchmark import compare_backends

  comparison = compare_backends(
      nx=64, ny=64, steps=100,
      backends=[Backend.SCALAR, Backend.SIMD, Backend.OMP]
  )
  # Shows speedup ratios
  ```

### Success Criteria

- Users can easily measure performance
- Backend comparisons help choose optimal configuration
- Timing data included in simulation results

---

## Phase 14: Async/Parallel Simulation

**Priority:** P3 - Advanced use case
**Estimated Effort:** 3-5 days

### Goals

- Support running multiple simulations in parallel
- Async API for non-blocking operations
- Progress callbacks for long-running simulations

### Tasks

- [ ] **14.1 Add progress callback support**
  ```python
  def progress_callback(step: int, total: int, stats: dict):
      print(f"Step {step}/{total}: max_vel={stats['max_velocity']:.4f}")

  run_simulation_with_params(..., callback=progress_callback, callback_interval=10)
  ```

- [ ] **14.2 Create async simulation wrapper**
  ```python
  import asyncio

  async def run_simulation_async(...) -> SimulationResult:
      """Run simulation in background thread."""
      loop = asyncio.get_event_loop()
      return await loop.run_in_executor(None, run_simulation_with_params, ...)
  ```

- [ ] **14.3 Add parameter sweep utility**
  ```python
  from cfd_python.parallel import parameter_sweep

  results = parameter_sweep(
      base_params={'nx': 64, 'ny': 64, 'steps': 100},
      vary={'dt': [0.001, 0.0005, 0.0001], 'cfl': [0.5, 0.8]},
      n_workers=4
  )
  ```

### Success Criteria

- Long simulations can report progress
- Multiple simulations can run in parallel
- Parameter sweeps are easy to set up

---

## Phase 15: 3D Grid Support

**Priority:** P2 - Extends core functionality
**Estimated Effort:** 5-7 days

### Goals

- Support 3D computational grids
- Extend boundary conditions to 3D
- Enable 3D flow simulations

### Tasks

- [ ] **15.1 Expose 3D grid functions from C library**
  ```python
  def create_grid_3d(
      nx: int, ny: int, nz: int,
      xmin: float, xmax: float,
      ymin: float, ymax: float,
      zmin: float, zmax: float
  ) -> dict: ...
  ```

- [ ] **15.2 Add 3D boundary condition edges**
  ```python
  class BCFace(IntEnum):
      """3D boundary faces."""
      WEST = 0    # -x
      EAST = 1    # +x
      SOUTH = 2   # -y
      NORTH = 3   # +y
      BOTTOM = 4  # -z
      TOP = 5     # +z
  ```

- [ ] **15.3 Extend Field class for 3D**
  ```python
  class Field3D(Field):
      def __init__(self, data: List[float], nx: int, ny: int, nz: int):
          self.nz = nz
          super().__init__(data, nx, ny)

      @property
      def shape(self) -> tuple[int, int, int]:
          return (self.nx, self.ny, self.nz)
  ```

- [ ] **15.4 Add 3D VTK output support**

- [ ] **15.5 Add 3D examples and tests**

### Success Criteria

- 3D grids can be created and manipulated
- Boundary conditions work on all 6 faces
- VTK output produces valid 3D visualizations

---

## Phase 16: Checkpoint & Restart

**Priority:** P2 - Important for long simulations
**Estimated Effort:** 2-3 days

### Goals

- Save simulation state to disk
- Resume interrupted simulations
- Support HDF5 format for efficient I/O

### Tasks

- [ ] **16.1 Add checkpoint save/load functions**
  ```python
  def save_checkpoint(
      filename: str,
      u: List[float], v: List[float], p: List[float],
      grid: Grid,
      step: int,
      time: float,
      params: dict
  ) -> None: ...

  def load_checkpoint(filename: str) -> dict:
      """Returns dict with all fields, grid, step, time, params."""
      ...
  ```

- [ ] **16.2 Add automatic checkpointing to Simulation class**
  ```python
  sim = Simulation(grid)
  sim.run(
      steps=10000,
      checkpoint_interval=1000,
      checkpoint_dir="./checkpoints"
  )
  ```

- [ ] **16.3 Add resume functionality**
  ```python
  sim = Simulation.from_checkpoint("./checkpoints/step_5000.h5")
  sim.run(steps=5000)  # Continues from step 5000
  ```

- [ ] **16.4 Optional HDF5 support**
  ```toml
  [project.optional-dependencies]
  hdf5 = ["h5py>=3.0"]
  ```

### Success Criteria

- Long simulations can be checkpointed
- Simulations can be resumed from checkpoints
- Checkpoint files are portable across platforms

---

## Phase 17: Validation Test Suite

**Priority:** P1 - Quality assurance
**Estimated Effort:** 3-4 days

### Goals

- Validate solver accuracy against known solutions
- Benchmark against analytical results
- Ensure numerical correctness across backends

### Tasks

- [ ] **17.1 Implement lid-driven cavity benchmark**
  ```python
  from cfd_python.validation import lid_driven_cavity

  results = lid_driven_cavity(
      Re=100,
      grid_sizes=[32, 64, 128],
      compare_ghia=True  # Compare to Ghia et al. (1982) reference data
  )
  results.plot_convergence()
  ```

- [ ] **17.2 Implement Poiseuille flow validation**
  ```python
  from cfd_python.validation import poiseuille_flow

  results = poiseuille_flow(
      nx=64, ny=32,
      pressure_gradient=0.1
  )
  error = results.compare_analytical()  # Should be < 1e-6
  ```

- [ ] **17.3 Implement Taylor-Green vortex decay**
  ```python
  from cfd_python.validation import taylor_green_vortex

  results = taylor_green_vortex(
      Re=100,
      grid_size=64,
      end_time=1.0
  )
  results.plot_energy_decay()
  ```

- [ ] **17.4 Add regression test suite**
  - Store reference results for each validation case
  - Fail CI if results deviate beyond tolerance

- [ ] **17.5 Backend consistency tests**
  - Ensure SCALAR, SIMD, OMP produce identical results
  - Verify CUDA results match CPU within tolerance

### Success Criteria

- All validation cases match reference data
- Regression tests catch numerical changes
- Backend consistency is verified automatically

---

## Phase 18: Jupyter Integration

**Priority:** P3 - Enhanced interactivity
**Estimated Effort:** 1-2 days

### Goals

- Rich display in Jupyter notebooks for simulation objects
- Interactive widgets for parameter exploration

### Note

Visualization-related Jupyter features (plots, animations, interactive dashboards) are handled by `cfd-visualization`.
See [cfd-visualization ROADMAP](../cfd-visualization/ROADMAP.md) Phase 2 for visualization in Jupyter.

### Tasks

- [ ] **18.1 Add `_repr_html_` for key classes**

  ```python
  class Grid:
      def _repr_html_(self) -> str:
          return f"""
          <div style="border: 1px solid #ccc; padding: 10px;">
              <b>Grid</b>: {self.nx} × {self.ny}<br>
              Domain: [{self._data['xmin']}, {self._data['xmax']}] ×
                      [{self._data['ymin']}, {self._data['ymax']}]
          </div>
          """

  class SimulationResult:
      def _repr_html_(self) -> str:
          return f"""
          <div style="border: 1px solid #ccc; padding: 10px;">
              <b>SimulationResult</b><br>
              Grid: {self.nx} × {self.ny}<br>
              Max velocity: {self.stats['max_velocity']:.4f}<br>
              Iterations: {self.stats['iterations']}
          </div>
          """
  ```

- [ ] **18.2 Add interactive parameter widgets**

  ```python
  from cfd_python.jupyter import interactive_simulation

  # Creates sliders for Re, dt, grid size
  interactive_simulation(
      solver="projection",
      Re_range=(10, 1000),
      grid_range=(16, 128)
  )
  ```

- [ ] **18.3 Add ipywidgets optional dependency**

  ```toml
  [project.optional-dependencies]
  jupyter = ["ipywidgets>=8.0"]
  ```

### Success Criteria

- Grid and SimulationResult display nicely in Jupyter
- Interactive widgets work for parameter exploration

---

## Phase 19: Configuration File Support

**Priority:** P3 - Usability improvement
**Estimated Effort:** 1-2 days

### Goals

- Define simulations via YAML/TOML config files
- Reproducible simulation setup
- Command-line interface for batch runs

### Tasks

- [ ] **19.1 Define configuration schema**
  ```yaml
  # simulation.yaml
  grid:
    nx: 64
    ny: 64
    domain:
      xmin: 0.0
      xmax: 1.0
      ymin: 0.0
      ymax: 1.0
    stretching: null

  solver:
    type: projection
    params:
      dt: 0.001
      cfl: 0.5
      max_iter: 1000
      tolerance: 1e-6

  boundary_conditions:
    left:
      type: inlet
      profile: parabolic
      max_velocity: 1.0
    right:
      type: outlet
    top:
      type: noslip
    bottom:
      type: noslip

  output:
    directory: ./results
    format: vtk
    interval: 100

  run:
    steps: 10000
    checkpoint_interval: 1000
  ```

- [ ] **19.2 Create config loader**
  ```python
  from cfd_python.config import load_config, run_from_config

  config = load_config("simulation.yaml")
  result = run_from_config(config)
  ```

- [ ] **19.3 Add CLI entry point**
  ```bash
  $ cfd-python run simulation.yaml
  $ cfd-python validate simulation.yaml
  $ cfd-python info  # Show available solvers, backends
  ```

- [ ] **19.4 Config validation with helpful errors**

### Success Criteria

- Simulations can be fully defined in config files
- CLI enables batch processing
- Config errors give clear, actionable messages

---

## Phase 20: Plugin Architecture

**Priority:** P4 - Extensibility
**Estimated Effort:** 3-5 days

### Goals

- Allow users to register custom solvers
- Support custom boundary conditions
- Enable third-party extensions

### Tasks

- [ ] **20.1 Define plugin interface**
  ```python
  from cfd_python.plugins import SolverPlugin, register_plugin

  class MySolver(SolverPlugin):
      name = "my_custom_solver"

      def step(self, u, v, p, dt):
          # Custom solver implementation
          ...

  register_plugin(MySolver)
  ```

- [ ] **20.2 Plugin discovery mechanism**
  ```python
  # Automatic discovery via entry points
  # pyproject.toml of plugin package:
  [project.entry-points."cfd_python.plugins"]
  my_solver = "my_package:MySolver"
  ```

- [ ] **20.3 Custom BC plugin support**
  ```python
  from cfd_python.plugins import BCPlugin

  class RotatingWall(BCPlugin):
      name = "rotating_wall"

      def apply(self, u, v, nx, ny, edge, omega):
          # Rotating wall BC implementation
          ...
  ```

- [ ] **20.4 Plugin validation and testing utilities**

### Success Criteria

- Users can create and register custom solvers
- Plugins discovered automatically via entry points
- Plugin API is stable and documented

---

## Phase 21: Memory Optimization

**Priority:** P2 - Performance
**Estimated Effort:** 2-3 days

### Goals

- Reduce memory footprint for large simulations
- Support memory-mapped arrays
- Enable out-of-core processing

### Tasks

- [ ] **21.1 Add memory usage reporting**
  ```python
  from cfd_python.memory import estimate_memory, get_memory_usage

  mem = estimate_memory(nx=1024, ny=1024, solver="projection")
  print(f"Estimated memory: {mem / 1e9:.2f} GB")

  # During simulation
  usage = get_memory_usage()
  print(f"Current usage: {usage['allocated_mb']:.1f} MB")
  ```

- [ ] **21.2 Memory-mapped field storage**
  ```python
  grid = Grid(nx=4096, ny=4096)
  sim = Simulation(grid, memory_mode="mmap", mmap_dir="/tmp/cfd")
  ```

- [ ] **21.3 Streaming output for large simulations**
  - Write output incrementally instead of buffering
  - Support compressed output formats

- [ ] **21.4 Memory pool for repeated allocations**

### Success Criteria

- Memory usage is predictable and reportable
- Large simulations can run with limited RAM
- No memory leaks in long-running simulations

---

## Phase 22: GPU Memory Management

**Priority:** P3 - CUDA enhancement
**Estimated Effort:** 2-3 days

### Goals

- Expose GPU memory information
- Support multi-GPU configurations
- Optimize GPU memory transfers

### Tasks

- [ ] **22.1 GPU memory reporting**
  ```python
  from cfd_python.cuda import get_gpu_info, get_gpu_memory

  info = get_gpu_info()
  # {'device_count': 2, 'devices': [{'name': 'RTX 4090', ...}, ...]}

  mem = get_gpu_memory(device=0)
  # {'total_mb': 24576, 'free_mb': 20000, 'used_mb': 4576}
  ```

- [ ] **22.2 Device selection**
  ```python
  from cfd_python.cuda import set_device

  set_device(1)  # Use second GPU
  sim.run(steps=1000)  # Runs on GPU 1
  ```

- [ ] **22.3 Multi-GPU domain decomposition**
  ```python
  sim = Simulation(
      grid,
      solver="projection_cuda",
      devices=[0, 1],  # Split across 2 GPUs
      decomposition="y"  # Split along y-axis
  )
  ```

- [ ] **22.4 Pinned memory for faster transfers**

### Success Criteria

- GPU memory usage is visible and controllable
- Multi-GPU runs work correctly
- Memory transfers are optimized

---

## Phase 23: Logging & Observability

**Priority:** P2 - Debugging and monitoring
**Estimated Effort:** 1-2 days

### Goals

- Structured logging throughout the library
- Integration with Python logging
- Performance metrics collection

### Tasks

- [ ] **23.1 Add structured logging**
  ```python
  import logging
  logging.basicConfig(level=logging.INFO)

  # cfd_python will now log:
  # INFO:cfd_python:Starting simulation with projection solver
  # INFO:cfd_python:Step 100/1000, max_vel=1.234, residual=1.2e-5
  ```

- [ ] **23.2 Configurable log levels**
  ```python
  import cfd_python
  cfd_python.set_log_level("DEBUG")  # Verbose output
  cfd_python.set_log_level("WARNING")  # Only warnings and errors
  ```

- [ ] **23.3 Metrics collection**
  ```python
  from cfd_python.metrics import get_metrics

  sim.run(steps=1000, collect_metrics=True)

  metrics = get_metrics()
  # {'solver_time_ms': [...], 'bc_time_ms': [...], 'memory_mb': [...]}
  ```

- [ ] **23.4 Integration with OpenTelemetry (optional)**

### Success Criteria

- Logging works with standard Python logging
- Debug information helps troubleshoot issues
- Metrics enable performance analysis

---

## Phase 24: Documentation Site

**Priority:** P1 - User adoption
**Estimated Effort:** 3-5 days

### Goals

- Comprehensive API documentation
- Tutorials and guides
- Searchable documentation site

### Tasks

- [ ] **24.1 Set up Sphinx documentation**
  - API reference from docstrings
  - Getting started guide
  - Installation instructions

- [ ] **24.2 Write tutorials**
  - Basic simulation walkthrough
  - Boundary conditions guide
  - Performance optimization tips
  - CUDA setup guide

- [ ] **24.3 Add example gallery**
  - Lid-driven cavity
  - Channel flow
  - Flow around cylinder
  - Heat transfer examples

- [ ] **24.4 Deploy to Read the Docs**

- [ ] **24.5 Add docstring coverage to CI**

### Success Criteria

- All public functions have docstrings
- Tutorials cover common use cases
- Documentation is searchable and navigable

---

## Version Planning

| Version | Phases | Focus |
|---------|--------|-------|
| 0.2.0 | 8, 9 | Type safety & IDE support |
| 0.3.0 | 10, 11 | High-level API & NumPy |
| 0.4.0 | 12, 13 | cfd-visualization integration & profiling |
| 0.5.0 | 14, 17 | Async, parallel & validation |
| 0.6.0 | 15, 16 | 3D support & checkpointing |
| 0.7.0 | 18, 19, 23 | Jupyter, config & logging |
| 0.8.0 | 20, 21, 22 | Plugins & memory optimization |
| 1.0.0 | 24 | Documentation & stabilization |

---

## Ideas Backlog

Items not yet planned but worth considering:

### Simulation Features
- [ ] Turbulence models (k-ε, k-ω, LES)
- [ ] Multiphase flow support
- [ ] Compressible flow solvers
- [ ] Thermal coupling (energy equation)
- [ ] Species transport
- [ ] Moving mesh support

### I/O & Interoperability
- [ ] OpenFOAM mesh import/export
- [ ] CGNS format support
- [ ] ParaView Catalyst integration
- [ ] NetCDF output format
- [ ] STL geometry import

### Performance
- [ ] Mixed precision (FP32/FP64)
- [ ] Sparse matrix solvers
- [ ] Multigrid preconditioners
- [ ] Domain decomposition for MPI

### Tooling

- [ ] VS Code extension
- [ ] PyCharm plugin
- [ ] Web-based simulation dashboard
- [ ] Docker images with pre-built CUDA support

---

## Contributing

Contributions are welcome! Priority areas:

1. **Type stubs** - Help complete the `.pyi` file
2. **Documentation** - Examples and tutorials
3. **Testing** - Edge cases and platform coverage
4. **Validation cases** - Add more benchmark problems

For visualization contributions, see [cfd-visualization](../cfd-visualization/ROADMAP.md).

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Related Documents

- [MIGRATION_PLAN.md](MIGRATION_PLAN.md) - Current v0.1.6 migration status
- [README.md](README.md) - User documentation
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [cfd-visualization ROADMAP](../cfd-visualization/ROADMAP.md) - Visualization library roadmap
