#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdio.h>
#include <stdlib.h>

// Include CFD library headers
#include "grid.h"
#include "solver_interface.h"
#include "simulation_api.h"
#include "vtk_output.h"
#include "csv_output.h"

/*
 * List available solvers
 */
static PyObject* list_solvers(PyObject* self, PyObject* args) {
    (void)self;
    (void)args;

    const char* names[32];
    int count = simulation_list_solvers(names, 32);

    PyObject* solver_list = PyList_New(count);
    for (int i = 0; i < count; i++) {
        PyList_SetItem(solver_list, i, PyUnicode_FromString(names[i]));
    }

    return solver_list;
}

/*
 * Check if a solver type is available
 */
static PyObject* has_solver(PyObject* self, PyObject* args) {
    (void)self;
    const char* solver_type;

    if (!PyArg_ParseTuple(args, "s", &solver_type)) {
        return NULL;
    }

    int available = simulation_has_solver(solver_type);
    return PyBool_FromLong(available);
}

/*
 * Get solver information
 */
static PyObject* get_solver_info(PyObject* self, PyObject* args) {
    (void)self;
    const char* solver_type;

    if (!PyArg_ParseTuple(args, "s", &solver_type)) {
        return NULL;
    }

    // Create a temporary solver to get its info
    Solver* solver = solver_create(solver_type);
    if (solver == NULL) {
        PyErr_Format(PyExc_ValueError, "Unknown solver type: %s", solver_type);
        return NULL;
    }

    PyObject* info = PyDict_New();
    PyDict_SetItemString(info, "name", PyUnicode_FromString(solver->name));
    PyDict_SetItemString(info, "description", PyUnicode_FromString(solver->description));
    PyDict_SetItemString(info, "version", PyUnicode_FromString(solver->version));

    // Build capabilities list
    PyObject* caps = PyList_New(0);
    if (solver->capabilities & SOLVER_CAP_INCOMPRESSIBLE) {
        PyList_Append(caps, PyUnicode_FromString("incompressible"));
    }
    if (solver->capabilities & SOLVER_CAP_COMPRESSIBLE) {
        PyList_Append(caps, PyUnicode_FromString("compressible"));
    }
    if (solver->capabilities & SOLVER_CAP_STEADY_STATE) {
        PyList_Append(caps, PyUnicode_FromString("steady_state"));
    }
    if (solver->capabilities & SOLVER_CAP_TRANSIENT) {
        PyList_Append(caps, PyUnicode_FromString("transient"));
    }
    if (solver->capabilities & SOLVER_CAP_SIMD) {
        PyList_Append(caps, PyUnicode_FromString("simd"));
    }
    if (solver->capabilities & SOLVER_CAP_PARALLEL) {
        PyList_Append(caps, PyUnicode_FromString("parallel"));
    }
    if (solver->capabilities & SOLVER_CAP_GPU) {
        PyList_Append(caps, PyUnicode_FromString("gpu"));
    }
    PyDict_SetItemString(info, "capabilities", caps);

    solver_destroy(solver);
    return info;
}

/*
 * Simple high-level run_simulation function
 */
static PyObject* run_simulation(PyObject* self, PyObject* args, PyObject* kwds) {
    (void)self;
    static char* kwlist[] = {"nx", "ny", "steps", "xmin", "xmax", "ymin", "ymax",
                             "solver_type", "output_file", NULL};
    size_t nx, ny, steps = 100;
    double xmin = 0.0, xmax = 1.0, ymin = 0.0, ymax = 1.0;
    const char* solver_type = NULL;
    const char* output_file = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "nn|nddddss", kwlist,
                                     &nx, &ny, &steps, &xmin, &xmax, &ymin, &ymax,
                                     &solver_type, &output_file)) {
        return NULL;
    }

    SimulationData* sim_data;
    if (solver_type) {
        sim_data = init_simulation_with_solver(nx, ny, xmin, xmax, ymin, ymax, solver_type);
    } else {
        sim_data = init_simulation(nx, ny, xmin, xmax, ymin, ymax);
    }

    if (sim_data == NULL) {
        if (solver_type) {
            PyErr_Format(PyExc_RuntimeError, "Failed to initialize simulation with solver '%s'", solver_type);
        } else {
            PyErr_SetString(PyExc_RuntimeError, "Failed to initialize simulation");
        }
        return NULL;
    }

    // Run simulation steps
    for (size_t i = 0; i < steps; i++) {
        run_simulation_step(sim_data);
    }

    // Write output if requested
    if (output_file) {
        write_vtk_flow_field(output_file, sim_data->field,
                            sim_data->grid->nx, sim_data->grid->ny,
                            sim_data->grid->xmin, sim_data->grid->xmax,
                            sim_data->grid->ymin, sim_data->grid->ymax);
    }

    // Get velocity magnitude for return
    FlowField* field = sim_data->field;
    double* vel_mag = calculate_velocity_magnitude(field, field->nx, field->ny);

    PyObject* result = NULL;
    if (vel_mag != NULL) {
        size_t size = field->nx * field->ny;
        result = PyList_New(size);
        for (size_t i = 0; i < size; i++) {
            PyList_SetItem(result, i, PyFloat_FromDouble(vel_mag[i]));
        }
        free(vel_mag);
    } else {
        result = PyList_New(0);
    }

    free_simulation(sim_data);
    return result;
}

/*
 * Create a simple grid function
 */
static PyObject* create_grid(PyObject* self, PyObject* args) {
    (void)self;
    size_t nx, ny;
    double xmin, xmax, ymin, ymax;

    if (!PyArg_ParseTuple(args, "nndddd", &nx, &ny, &xmin, &xmax, &ymin, &ymax)) {
        return NULL;
    }

    Grid* grid = grid_create(nx, ny, xmin, xmax, ymin, ymax);
    if (grid == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to create grid");
        return NULL;
    }

    grid_initialize_uniform(grid);

    // Return grid information as a dictionary
    PyObject* grid_dict = PyDict_New();
    PyDict_SetItemString(grid_dict, "nx", PyLong_FromSize_t(grid->nx));
    PyDict_SetItemString(grid_dict, "ny", PyLong_FromSize_t(grid->ny));
    PyDict_SetItemString(grid_dict, "xmin", PyFloat_FromDouble(grid->xmin));
    PyDict_SetItemString(grid_dict, "xmax", PyFloat_FromDouble(grid->xmax));
    PyDict_SetItemString(grid_dict, "ymin", PyFloat_FromDouble(grid->ymin));
    PyDict_SetItemString(grid_dict, "ymax", PyFloat_FromDouble(grid->ymax));

    // Create coordinate lists
    PyObject* x_list = PyList_New(grid->nx);
    PyObject* y_list = PyList_New(grid->ny);

    for (size_t i = 0; i < grid->nx; i++) {
        PyList_SetItem(x_list, i, PyFloat_FromDouble(grid->x[i]));
    }

    for (size_t i = 0; i < grid->ny; i++) {
        PyList_SetItem(y_list, i, PyFloat_FromDouble(grid->y[i]));
    }

    PyDict_SetItemString(grid_dict, "x_coords", x_list);
    PyDict_SetItemString(grid_dict, "y_coords", y_list);

    grid_destroy(grid);
    return grid_dict;
}

/*
 * Get default solver parameters
 */
static PyObject* get_default_solver_params(PyObject* self, PyObject* args) {
    (void)self;
    (void)args;
    SolverParams params = solver_params_default();

    PyObject* params_dict = PyDict_New();
    PyDict_SetItemString(params_dict, "dt", PyFloat_FromDouble(params.dt));
    PyDict_SetItemString(params_dict, "cfl", PyFloat_FromDouble(params.cfl));
    PyDict_SetItemString(params_dict, "gamma", PyFloat_FromDouble(params.gamma));
    PyDict_SetItemString(params_dict, "mu", PyFloat_FromDouble(params.mu));
    PyDict_SetItemString(params_dict, "k", PyFloat_FromDouble(params.k));
    PyDict_SetItemString(params_dict, "max_iter", PyLong_FromLong(params.max_iter));
    PyDict_SetItemString(params_dict, "tolerance", PyFloat_FromDouble(params.tolerance));

    return params_dict;
}

/*
 * Run simulation with detailed parameters and solver selection
 */
static PyObject* run_simulation_with_params(PyObject* self, PyObject* args, PyObject* kwds) {
    (void)self;
    static char* kwlist[] = {"nx", "ny", "xmin", "xmax", "ymin", "ymax",
                             "steps", "dt", "cfl", "solver_type", "output_file", NULL};
    size_t nx, ny, steps = 1;
    double xmin, xmax, ymin, ymax;
    double dt = 0.001, cfl = 0.2;
    const char* solver_type = NULL;
    const char* output_file = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "nndddd|nddss", kwlist,
                                     &nx, &ny, &xmin, &xmax, &ymin, &ymax,
                                     &steps, &dt, &cfl, &solver_type, &output_file)) {
        return NULL;
    }

    SimulationData* sim_data;
    if (solver_type) {
        sim_data = init_simulation_with_solver(nx, ny, xmin, xmax, ymin, ymax, solver_type);
    } else {
        sim_data = init_simulation(nx, ny, xmin, xmax, ymin, ymax);
    }

    if (sim_data == NULL) {
        if (solver_type) {
            PyErr_Format(PyExc_RuntimeError, "Failed to initialize simulation with solver '%s'", solver_type);
        } else {
            PyErr_SetString(PyExc_RuntimeError, "Failed to initialize simulation");
        }
        return NULL;
    }

    // Modify solver parameters
    sim_data->params.dt = dt;
    sim_data->params.cfl = cfl;

    // Run simulation steps
    for (size_t i = 0; i < steps; i++) {
        run_simulation_step(sim_data);
    }

    // Create results dictionary
    PyObject* results = PyDict_New();

    // Get velocity magnitude
    FlowField* field = sim_data->field;
    double* vel_mag = calculate_velocity_magnitude(field, field->nx, field->ny);

    if (vel_mag != NULL) {
        size_t size = field->nx * field->ny;
        PyObject* vel_list = PyList_New(size);
        for (size_t i = 0; i < size; i++) {
            PyList_SetItem(vel_list, i, PyFloat_FromDouble(vel_mag[i]));
        }
        PyDict_SetItemString(results, "velocity_magnitude", vel_list);
        free(vel_mag);
    }

    // Add simulation info
    PyDict_SetItemString(results, "nx", PyLong_FromSize_t(nx));
    PyDict_SetItemString(results, "ny", PyLong_FromSize_t(ny));
    PyDict_SetItemString(results, "steps", PyLong_FromSize_t(steps));

    // Add solver info
    Solver* solver = simulation_get_solver(sim_data);
    if (solver) {
        PyDict_SetItemString(results, "solver_name", PyUnicode_FromString(solver->name));
        PyDict_SetItemString(results, "solver_description", PyUnicode_FromString(solver->description));
    }

    // Add solver statistics
    const SolverStats* stats = simulation_get_stats(sim_data);
    if (stats) {
        PyObject* stats_dict = PyDict_New();
        PyDict_SetItemString(stats_dict, "iterations", PyLong_FromLong(stats->iterations));
        PyDict_SetItemString(stats_dict, "max_velocity", PyFloat_FromDouble(stats->max_velocity));
        PyDict_SetItemString(stats_dict, "max_pressure", PyFloat_FromDouble(stats->max_pressure));
        PyDict_SetItemString(stats_dict, "elapsed_time_ms", PyFloat_FromDouble(stats->elapsed_time_ms));
        PyDict_SetItemString(results, "stats", stats_dict);
    }

    // Write output if requested
    if (output_file) {
        write_vtk_flow_field(output_file, sim_data->field,
                            sim_data->grid->nx, sim_data->grid->ny,
                            sim_data->grid->xmin, sim_data->grid->xmax,
                            sim_data->grid->ymin, sim_data->grid->ymax);
        PyDict_SetItemString(results, "output_file", PyUnicode_FromString(output_file));
    }

    free_simulation(sim_data);
    return results;
}

/*
 * Set the output directory for simulation outputs
 */
static PyObject* set_output_dir(PyObject* self, PyObject* args) {
    (void)self;
    const char* output_dir;

    if (!PyArg_ParseTuple(args, "s", &output_dir)) {
        return NULL;
    }

    simulation_set_output_dir(output_dir);
    Py_RETURN_NONE;
}

/*
 * Write VTK scalar output
 */
static PyObject* write_vtk_scalar(PyObject* self, PyObject* args, PyObject* kwds) {
    (void)self;
    static char* kwlist[] = {"filename", "field_name", "data", "nx", "ny",
                             "xmin", "xmax", "ymin", "ymax", NULL};
    const char* filename;
    const char* field_name;
    PyObject* data_list;
    size_t nx, ny;
    double xmin, xmax, ymin, ymax;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "ssOnndddd", kwlist,
                                     &filename, &field_name, &data_list,
                                     &nx, &ny, &xmin, &xmax, &ymin, &ymax)) {
        return NULL;
    }

    // Convert Python list to C array
    if (!PyList_Check(data_list)) {
        PyErr_SetString(PyExc_TypeError, "data must be a list");
        return NULL;
    }

    size_t size = nx * ny;
    if ((size_t)PyList_Size(data_list) != size) {
        PyErr_Format(PyExc_ValueError, "data list size (%zd) must match nx*ny (%zu)",
                     PyList_Size(data_list), size);
        return NULL;
    }

    double* data = (double*)malloc(size * sizeof(double));
    if (data == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate data array");
        return NULL;
    }

    for (size_t i = 0; i < size; i++) {
        PyObject* item = PyList_GetItem(data_list, i);
        data[i] = PyFloat_AsDouble(item);
        if (PyErr_Occurred()) {
            free(data);
            return NULL;
        }
    }

    write_vtk_output(filename, field_name, data, nx, ny, xmin, xmax, ymin, ymax);
    free(data);

    Py_RETURN_NONE;
}

/*
 * Write VTK vector output
 */
static PyObject* write_vtk_vector(PyObject* self, PyObject* args, PyObject* kwds) {
    (void)self;
    static char* kwlist[] = {"filename", "field_name", "u_data", "v_data", "nx", "ny",
                             "xmin", "xmax", "ymin", "ymax", NULL};
    const char* filename;
    const char* field_name;
    PyObject* u_list;
    PyObject* v_list;
    size_t nx, ny;
    double xmin, xmax, ymin, ymax;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "ssOOnndddd", kwlist,
                                     &filename, &field_name, &u_list, &v_list,
                                     &nx, &ny, &xmin, &xmax, &ymin, &ymax)) {
        return NULL;
    }

    // Validate lists
    if (!PyList_Check(u_list) || !PyList_Check(v_list)) {
        PyErr_SetString(PyExc_TypeError, "u_data and v_data must be lists");
        return NULL;
    }

    size_t size = nx * ny;
    if ((size_t)PyList_Size(u_list) != size || (size_t)PyList_Size(v_list) != size) {
        PyErr_SetString(PyExc_ValueError, "data list sizes must match nx*ny");
        return NULL;
    }

    double* u_data = (double*)malloc(size * sizeof(double));
    double* v_data = (double*)malloc(size * sizeof(double));
    if (u_data == NULL || v_data == NULL) {
        free(u_data);
        free(v_data);
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate data arrays");
        return NULL;
    }

    for (size_t i = 0; i < size; i++) {
        u_data[i] = PyFloat_AsDouble(PyList_GetItem(u_list, i));
        v_data[i] = PyFloat_AsDouble(PyList_GetItem(v_list, i));
        if (PyErr_Occurred()) {
            free(u_data);
            free(v_data);
            return NULL;
        }
    }

    write_vtk_vector_output(filename, field_name, u_data, v_data, nx, ny, xmin, xmax, ymin, ymax);
    free(u_data);
    free(v_data);

    Py_RETURN_NONE;
}

/*
 * Write CSV timeseries data
 */
static PyObject* write_csv_timeseries_py(PyObject* self, PyObject* args, PyObject* kwds) {
    (void)self;
    static char* kwlist[] = {"filename", "step", "time", "u_data", "v_data", "p_data",
                             "nx", "ny", "dt", "iterations", "create_new", NULL};
    const char* filename;
    int step;
    double time;
    PyObject* u_list;
    PyObject* v_list;
    PyObject* p_list;
    size_t nx, ny;
    double dt;
    int iterations;
    int create_new = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "sidOOOnndip", kwlist,
                                     &filename, &step, &time, &u_list, &v_list, &p_list,
                                     &nx, &ny, &dt, &iterations, &create_new)) {
        return NULL;
    }

    size_t size = nx * ny;

    // Allocate and populate flow field
    FlowField* field = flow_field_create(nx, ny);
    if (field == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate flow field");
        return NULL;
    }

    for (size_t i = 0; i < size; i++) {
        field->u[i] = PyFloat_AsDouble(PyList_GetItem(u_list, i));
        field->v[i] = PyFloat_AsDouble(PyList_GetItem(v_list, i));
        field->p[i] = PyFloat_AsDouble(PyList_GetItem(p_list, i));
        if (PyErr_Occurred()) {
            flow_field_destroy(field);
            return NULL;
        }
    }

    SolverParams params = solver_params_default();
    params.dt = dt;

    SolverStats stats = solver_stats_default();
    stats.iterations = iterations;

    write_csv_timeseries(filename, step, time, field, &params, &stats, nx, ny, create_new);

    flow_field_destroy(field);
    Py_RETURN_NONE;
}

/*
 * Module definition
 */
static PyMethodDef cfd_python_methods[] = {
    {"run_simulation", (PyCFunction)run_simulation, METH_VARARGS | METH_KEYWORDS,
     "Run a complete CFD simulation.\n\n"
     "Args:\n"
     "    nx (int): Number of grid points in x direction\n"
     "    ny (int): Number of grid points in y direction\n"
     "    steps (int, optional): Number of time steps (default: 100)\n"
     "    xmin (float, optional): Minimum x coordinate (default: 0.0)\n"
     "    xmax (float, optional): Maximum x coordinate (default: 1.0)\n"
     "    ymin (float, optional): Minimum y coordinate (default: 0.0)\n"
     "    ymax (float, optional): Maximum y coordinate (default: 1.0)\n"
     "    solver_type (str, optional): Solver type name (default: 'explicit_euler')\n"
     "    output_file (str, optional): VTK output file path\n\n"
     "Returns:\n"
     "    list: Velocity magnitude values as a flat list"},
    {"create_grid", create_grid, METH_VARARGS,
     "Create a computational grid and return its properties.\n\n"
     "Args:\n"
     "    nx (int): Number of grid points in x direction\n"
     "    ny (int): Number of grid points in y direction\n"
     "    xmin (float): Minimum x coordinate\n"
     "    xmax (float): Maximum x coordinate\n"
     "    ymin (float): Minimum y coordinate\n"
     "    ymax (float): Maximum y coordinate\n\n"
     "Returns:\n"
     "    dict: Grid properties including coordinates"},
    {"get_default_solver_params", get_default_solver_params, METH_NOARGS,
     "Get default solver parameters as a dictionary.\n\n"
     "Returns:\n"
     "    dict: Default solver parameters (dt, cfl, gamma, mu, k, max_iter, tolerance)"},
    {"run_simulation_with_params", (PyCFunction)run_simulation_with_params, METH_VARARGS | METH_KEYWORDS,
     "Run simulation with custom parameters and return detailed results.\n\n"
     "Args:\n"
     "    nx (int): Number of grid points in x direction\n"
     "    ny (int): Number of grid points in y direction\n"
     "    xmin (float): Minimum x coordinate\n"
     "    xmax (float): Maximum x coordinate\n"
     "    ymin (float): Minimum y coordinate\n"
     "    ymax (float): Maximum y coordinate\n"
     "    steps (int, optional): Number of time steps (default: 1)\n"
     "    dt (float, optional): Time step size (default: 0.001)\n"
     "    cfl (float, optional): CFL number (default: 0.2)\n"
     "    solver_type (str, optional): Solver type name\n"
     "    output_file (str, optional): VTK output file path\n\n"
     "Returns:\n"
     "    dict: Results including velocity_magnitude, solver info, and stats"},
    {"list_solvers", list_solvers, METH_NOARGS,
     "List available solver types.\n\n"
     "Returns:\n"
     "    list: Names of available solvers"},
    {"has_solver", has_solver, METH_VARARGS,
     "Check if a solver type is available.\n\n"
     "Args:\n"
     "    solver_type (str): Name of the solver type\n\n"
     "Returns:\n"
     "    bool: True if solver is available"},
    {"get_solver_info", get_solver_info, METH_VARARGS,
     "Get information about a solver type.\n\n"
     "Args:\n"
     "    solver_type (str): Name of the solver type\n\n"
     "Returns:\n"
     "    dict: Solver info (name, description, version, capabilities)"},
    {"set_output_dir", set_output_dir, METH_VARARGS,
     "Set the base output directory for simulation outputs.\n\n"
     "Args:\n"
     "    output_dir (str): Base directory path for outputs"},
    {"write_vtk_scalar", (PyCFunction)write_vtk_scalar, METH_VARARGS | METH_KEYWORDS,
     "Write scalar field data to VTK file.\n\n"
     "Args:\n"
     "    filename (str): Output file path\n"
     "    field_name (str): Name of the scalar field\n"
     "    data (list): Flat list of scalar values (nx*ny)\n"
     "    nx (int): Grid points in x direction\n"
     "    ny (int): Grid points in y direction\n"
     "    xmin, xmax, ymin, ymax (float): Domain bounds"},
    {"write_vtk_vector", (PyCFunction)write_vtk_vector, METH_VARARGS | METH_KEYWORDS,
     "Write vector field data to VTK file.\n\n"
     "Args:\n"
     "    filename (str): Output file path\n"
     "    field_name (str): Name of the vector field\n"
     "    u_data (list): Flat list of u-component values\n"
     "    v_data (list): Flat list of v-component values\n"
     "    nx (int): Grid points in x direction\n"
     "    ny (int): Grid points in y direction\n"
     "    xmin, xmax, ymin, ymax (float): Domain bounds"},
    {"write_csv_timeseries", (PyCFunction)write_csv_timeseries_py, METH_VARARGS | METH_KEYWORDS,
     "Write simulation timeseries data to CSV file.\n\n"
     "Args:\n"
     "    filename (str): Output file path\n"
     "    step (int): Current simulation step\n"
     "    time (float): Current simulation time\n"
     "    u_data, v_data, p_data (list): Flow field data\n"
     "    nx, ny (int): Grid dimensions\n"
     "    dt (float): Time step size\n"
     "    iterations (int): Solver iterations\n"
     "    create_new (bool): True to create new file, False to append"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef cfd_python_module = {
    PyModuleDef_HEAD_INIT,
    "cfd_python",
    "Python bindings for CFD simulation library with pluggable solver support.\n\n"
    "Available functions:\n"
    "  - list_solvers(): Get available solver types\n"
    "  - has_solver(name): Check if a solver exists\n"
    "  - get_solver_info(name): Get solver details\n"
    "  - run_simulation(...): Run a simulation\n"
    "  - run_simulation_with_params(...): Run with detailed parameters\n"
    "  - create_grid(...): Create a computational grid\n"
    "  - get_default_solver_params(): Get default parameters\n"
    "  - set_output_dir(path): Set output directory\n"
    "  - write_vtk_scalar(...): Write scalar VTK output\n"
    "  - write_vtk_vector(...): Write vector VTK output\n"
    "  - write_csv_timeseries(...): Write CSV timeseries\n\n"
    "Available solver types:\n"
    "  - 'explicit_euler': Basic finite difference solver\n"
    "  - 'explicit_euler_optimized': SIMD-optimized solver\n"
    "  - 'projection': Pressure-velocity projection solver\n"
    "  - 'projection_optimized': Optimized projection solver\n"
    "  - 'explicit_euler_gpu': GPU-accelerated Euler solver\n"
    "  - 'projection_jacobi_gpu': GPU-accelerated projection solver",
    -1,
    cfd_python_methods
};

PyMODINIT_FUNC PyInit_cfd_python(void) {
    PyObject* m = PyModule_Create(&cfd_python_module);
    if (m == NULL) {
        return NULL;
    }

    // Add version info
    PyModule_AddStringConstant(m, "__version__", "0.3.0");

    // Initialize the solver registry so solvers are available
    solver_registry_init();

    // Dynamically add solver type constants from the registry
    // This automatically picks up any new solvers added to the C library
    const char* solver_names[32];
    int solver_count = solver_registry_list(solver_names, 32);
    for (int i = 0; i < solver_count; i++) {
        // Convert solver name to uppercase constant name
        // e.g., "explicit_euler" -> "SOLVER_EXPLICIT_EULER"
        char const_name[64] = "SOLVER_";
        size_t prefix_len = 7;
        size_t j = 0;
        while (solver_names[i][j] != '\0' && prefix_len + j < 63) {
            char c = solver_names[i][j];
            if (c >= 'a' && c <= 'z') {
                const_name[prefix_len + j] = c - 'a' + 'A';  // to uppercase
            } else {
                const_name[prefix_len + j] = c;
            }
            j++;
        }
        const_name[prefix_len + j] = '\0';
        PyModule_AddStringConstant(m, const_name, solver_names[i]);
    }

    // Add output field type constants (these are defined in simulation_api.h enum)
    PyModule_AddIntConstant(m, "OUTPUT_PRESSURE", OUTPUT_PRESSURE);
    PyModule_AddIntConstant(m, "OUTPUT_VELOCITY", OUTPUT_VELOCITY);
    PyModule_AddIntConstant(m, "OUTPUT_FULL_FIELD", OUTPUT_FULL_FIELD);
    PyModule_AddIntConstant(m, "OUTPUT_CSV_TIMESERIES", OUTPUT_CSV_TIMESERIES);
    PyModule_AddIntConstant(m, "OUTPUT_CSV_CENTERLINE", OUTPUT_CSV_CENTERLINE);
    PyModule_AddIntConstant(m, "OUTPUT_CSV_STATISTICS", OUTPUT_CSV_STATISTICS);

    return m;
}
