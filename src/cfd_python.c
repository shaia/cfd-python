// Py_LIMITED_API should be defined via build system (CMake) before including Python.h
// for stable ABI support. The CMake option CFD_USE_STABLE_ABI controls this.
// When enabled, it targets Python 3.8+ stable ABI (0x03080000) for binary compatibility
// across Python versions. Do NOT define it here unconditionally as it requires linking
// against python3.lib which may not be available in all environments.

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

    PyObject* solver_list = PyList_New(0);
    if (solver_list == NULL) {
        return NULL;
    }
    for (int i = 0; i < count; i++) {
        PyObject* name = PyUnicode_FromString(names[i]);
        if (name == NULL || PyList_Append(solver_list, name) < 0) {
            Py_XDECREF(name);
            Py_DECREF(solver_list);
            return NULL;
        }
        Py_DECREF(name);
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
    if (info == NULL) {
        solver_destroy(solver);
        return NULL;
    }

    // Helper macro to add string to dict with proper refcount
    #define ADD_STRING_TO_DICT(dict, key, value) do { \
        PyObject* tmp = PyUnicode_FromString(value); \
        if (tmp == NULL) { Py_DECREF(dict); solver_destroy(solver); return NULL; } \
        PyDict_SetItemString(dict, key, tmp); \
        Py_DECREF(tmp); \
    } while(0)

    ADD_STRING_TO_DICT(info, "name", solver->name);
    ADD_STRING_TO_DICT(info, "description", solver->description);
    ADD_STRING_TO_DICT(info, "version", solver->version);

    #undef ADD_STRING_TO_DICT

    // Build capabilities list
    PyObject* caps = PyList_New(0);
    if (caps == NULL) {
        Py_DECREF(info);
        solver_destroy(solver);
        return NULL;
    }

    // Helper macro to append capability string
    #define APPEND_CAP(list, cap_flag, cap_name) do { \
        if (solver->capabilities & cap_flag) { \
            PyObject* s = PyUnicode_FromString(cap_name); \
            if (s == NULL || PyList_Append(list, s) < 0) { \
                Py_XDECREF(s); Py_DECREF(list); Py_DECREF(info); \
                solver_destroy(solver); return NULL; \
            } \
            Py_DECREF(s); \
        } \
    } while(0)

    APPEND_CAP(caps, SOLVER_CAP_INCOMPRESSIBLE, "incompressible");
    APPEND_CAP(caps, SOLVER_CAP_COMPRESSIBLE, "compressible");
    APPEND_CAP(caps, SOLVER_CAP_STEADY_STATE, "steady_state");
    APPEND_CAP(caps, SOLVER_CAP_TRANSIENT, "transient");
    APPEND_CAP(caps, SOLVER_CAP_SIMD, "simd");
    APPEND_CAP(caps, SOLVER_CAP_PARALLEL, "parallel");
    APPEND_CAP(caps, SOLVER_CAP_GPU, "gpu");

    #undef APPEND_CAP

    PyDict_SetItemString(info, "capabilities", caps);
    Py_DECREF(caps);

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

    PyObject* result = PyList_New(0);
    if (result == NULL) {
        free(vel_mag);
        free_simulation(sim_data);
        return NULL;
    }

    if (vel_mag != NULL) {
        size_t size = field->nx * field->ny;
        for (size_t i = 0; i < size; i++) {
            PyObject* val = PyFloat_FromDouble(vel_mag[i]);
            if (val == NULL || PyList_Append(result, val) < 0) {
                Py_XDECREF(val);
                Py_DECREF(result);
                free(vel_mag);
                free_simulation(sim_data);
                return NULL;
            }
            Py_DECREF(val);
        }
        free(vel_mag);
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
    if (grid_dict == NULL) {
        grid_destroy(grid);
        return NULL;
    }

    // Helper macro to add values to dict with proper refcount
    #define ADD_TO_DICT(dict, key, py_val) do { \
        PyObject* tmp = (py_val); \
        if (tmp == NULL) { Py_DECREF(dict); grid_destroy(grid); return NULL; } \
        PyDict_SetItemString(dict, key, tmp); \
        Py_DECREF(tmp); \
    } while(0)

    ADD_TO_DICT(grid_dict, "nx", PyLong_FromSize_t(grid->nx));
    ADD_TO_DICT(grid_dict, "ny", PyLong_FromSize_t(grid->ny));
    ADD_TO_DICT(grid_dict, "xmin", PyFloat_FromDouble(grid->xmin));
    ADD_TO_DICT(grid_dict, "xmax", PyFloat_FromDouble(grid->xmax));
    ADD_TO_DICT(grid_dict, "ymin", PyFloat_FromDouble(grid->ymin));
    ADD_TO_DICT(grid_dict, "ymax", PyFloat_FromDouble(grid->ymax));

    #undef ADD_TO_DICT

    // Create coordinate lists
    PyObject* x_list = PyList_New(0);
    PyObject* y_list = PyList_New(0);
    if (x_list == NULL || y_list == NULL) {
        Py_XDECREF(x_list);
        Py_XDECREF(y_list);
        Py_DECREF(grid_dict);
        grid_destroy(grid);
        return NULL;
    }

    for (size_t i = 0; i < grid->nx; i++) {
        PyObject* val = PyFloat_FromDouble(grid->x[i]);
        if (val == NULL || PyList_Append(x_list, val) < 0) {
            Py_XDECREF(val);
            Py_DECREF(x_list);
            Py_DECREF(y_list);
            Py_DECREF(grid_dict);
            grid_destroy(grid);
            return NULL;
        }
        Py_DECREF(val);
    }

    for (size_t i = 0; i < grid->ny; i++) {
        PyObject* val = PyFloat_FromDouble(grid->y[i]);
        if (val == NULL || PyList_Append(y_list, val) < 0) {
            Py_XDECREF(val);
            Py_DECREF(x_list);
            Py_DECREF(y_list);
            Py_DECREF(grid_dict);
            grid_destroy(grid);
            return NULL;
        }
        Py_DECREF(val);
    }

    PyDict_SetItemString(grid_dict, "x_coords", x_list);
    PyDict_SetItemString(grid_dict, "y_coords", y_list);
    Py_DECREF(x_list);
    Py_DECREF(y_list);

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
    if (params_dict == NULL) {
        return NULL;
    }

    // Helper macro to add values to dict with proper refcount
    #define ADD_TO_DICT(dict, key, py_val) do { \
        PyObject* tmp = (py_val); \
        if (tmp == NULL) { Py_DECREF(dict); return NULL; } \
        PyDict_SetItemString(dict, key, tmp); \
        Py_DECREF(tmp); \
    } while(0)

    ADD_TO_DICT(params_dict, "dt", PyFloat_FromDouble(params.dt));
    ADD_TO_DICT(params_dict, "cfl", PyFloat_FromDouble(params.cfl));
    ADD_TO_DICT(params_dict, "gamma", PyFloat_FromDouble(params.gamma));
    ADD_TO_DICT(params_dict, "mu", PyFloat_FromDouble(params.mu));
    ADD_TO_DICT(params_dict, "k", PyFloat_FromDouble(params.k));
    ADD_TO_DICT(params_dict, "max_iter", PyLong_FromLong(params.max_iter));
    ADD_TO_DICT(params_dict, "tolerance", PyFloat_FromDouble(params.tolerance));

    #undef ADD_TO_DICT

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
    if (results == NULL) {
        free_simulation(sim_data);
        return NULL;
    }

    // Get velocity magnitude
    FlowField* field = sim_data->field;
    double* vel_mag = calculate_velocity_magnitude(field, field->nx, field->ny);

    if (vel_mag != NULL) {
        size_t size = field->nx * field->ny;
        PyObject* vel_list = PyList_New(0);
        if (vel_list == NULL) {
            free(vel_mag);
            Py_DECREF(results);
            free_simulation(sim_data);
            return NULL;
        }
        for (size_t i = 0; i < size; i++) {
            PyObject* val = PyFloat_FromDouble(vel_mag[i]);
            if (val == NULL || PyList_Append(vel_list, val) < 0) {
                Py_XDECREF(val);
                Py_DECREF(vel_list);
                Py_DECREF(results);
                free(vel_mag);
                free_simulation(sim_data);
                return NULL;
            }
            Py_DECREF(val);
        }
        PyDict_SetItemString(results, "velocity_magnitude", vel_list);
        Py_DECREF(vel_list);
        free(vel_mag);
    }

    // Helper macro to add values to dict with proper refcount
    #define ADD_TO_DICT(dict, key, py_val) do { \
        PyObject* tmp = (py_val); \
        if (tmp == NULL) { Py_DECREF(dict); free_simulation(sim_data); return NULL; } \
        PyDict_SetItemString(dict, key, tmp); \
        Py_DECREF(tmp); \
    } while(0)

    // Add simulation info
    ADD_TO_DICT(results, "nx", PyLong_FromSize_t(nx));
    ADD_TO_DICT(results, "ny", PyLong_FromSize_t(ny));
    ADD_TO_DICT(results, "steps", PyLong_FromSize_t(steps));

    // Add solver info
    Solver* solver = simulation_get_solver(sim_data);
    if (solver) {
        ADD_TO_DICT(results, "solver_name", PyUnicode_FromString(solver->name));
        ADD_TO_DICT(results, "solver_description", PyUnicode_FromString(solver->description));
    }

    // Add solver statistics
    const SolverStats* stats = simulation_get_stats(sim_data);
    if (stats) {
        PyObject* stats_dict = PyDict_New();
        if (stats_dict == NULL) {
            Py_DECREF(results);
            free_simulation(sim_data);
            return NULL;
        }

        // Use a local macro for stats_dict
        #define ADD_TO_STATS(key, py_val) do { \
            PyObject* tmp = (py_val); \
            if (tmp == NULL) { Py_DECREF(stats_dict); Py_DECREF(results); free_simulation(sim_data); return NULL; } \
            PyDict_SetItemString(stats_dict, key, tmp); \
            Py_DECREF(tmp); \
        } while(0)

        ADD_TO_STATS("iterations", PyLong_FromLong(stats->iterations));
        ADD_TO_STATS("max_velocity", PyFloat_FromDouble(stats->max_velocity));
        ADD_TO_STATS("max_pressure", PyFloat_FromDouble(stats->max_pressure));
        ADD_TO_STATS("elapsed_time_ms", PyFloat_FromDouble(stats->elapsed_time_ms));

        #undef ADD_TO_STATS

        PyDict_SetItemString(results, "stats", stats_dict);
        Py_DECREF(stats_dict);
    }

    #undef ADD_TO_DICT

    // Write output if requested
    if (output_file) {
        write_vtk_flow_field(output_file, sim_data->field,
                            sim_data->grid->nx, sim_data->grid->ny,
                            sim_data->grid->xmin, sim_data->grid->xmax,
                            sim_data->grid->ymin, sim_data->grid->ymax);
        PyObject* output_str = PyUnicode_FromString(output_file);
        if (output_str != NULL) {
            PyDict_SetItemString(results, "output_file", output_str);
            Py_DECREF(output_str);
        }
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
        if (item == NULL) {
            free(data);
            return NULL;
        }
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

    double* u_data = NULL;
    double* v_data = NULL;

    u_data = (double*)malloc(size * sizeof(double));
    v_data = (double*)malloc(size * sizeof(double));
    if (u_data == NULL || v_data == NULL) {
        free(u_data);
        free(v_data);
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate data arrays");
        return NULL;
    }

    for (size_t i = 0; i < size; i++) {
        PyObject* u_item = PyList_GetItem(u_list, i);
        PyObject* v_item = PyList_GetItem(v_list, i);
        if (u_item == NULL || v_item == NULL) {
            free(u_data);
            free(v_data);
            return NULL;
        }
        u_data[i] = PyFloat_AsDouble(u_item);
        v_data[i] = PyFloat_AsDouble(v_item);
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

    // Validate lists
    if (!PyList_Check(u_list) || !PyList_Check(v_list) || !PyList_Check(p_list)) {
        PyErr_SetString(PyExc_TypeError, "u_data, v_data, and p_data must be lists");
        return NULL;
    }

    size_t size = nx * ny;
    if ((size_t)PyList_Size(u_list) != size || (size_t)PyList_Size(v_list) != size ||
        (size_t)PyList_Size(p_list) != size) {
        PyErr_SetString(PyExc_ValueError, "data list sizes must match nx*ny");
        return NULL;
    }

    // Allocate and populate flow field
    FlowField* field = flow_field_create(nx, ny);
    if (field == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate flow field");
        return NULL;
    }

    for (size_t i = 0; i < size; i++) {
        PyObject* u_item = PyList_GetItem(u_list, i);
        PyObject* v_item = PyList_GetItem(v_list, i);
        PyObject* p_item = PyList_GetItem(p_list, i);
        if (u_item == NULL || v_item == NULL || p_item == NULL) {
            flow_field_destroy(field);
            return NULL;
        }
        field->u[i] = PyFloat_AsDouble(u_item);
        field->v[i] = PyFloat_AsDouble(v_item);
        field->p[i] = PyFloat_AsDouble(p_item);
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
     "    solver_type (str, optional): Solver type name (uses library default if not specified)\n"
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
    if (PyModule_AddStringConstant(m, "__version__", "0.3.0") < 0) {
        Py_DECREF(m);
        return NULL;
    }

    // Initialize the solver registry so solvers are available
    solver_registry_init();

    // Dynamically add solver type constants from the registry
    // This automatically picks up any new solvers added to the C library
    const char* solver_names[32];
    int solver_count = solver_registry_list(solver_names, 32);
    for (int i = 0; i < solver_count; i++) {
        // Convert solver name to uppercase constant name
        // e.g., "explicit_euler" -> "SOLVER_EXPLICIT_EULER"
        // Buffer: 64 bytes, prefix "SOLVER_" = 7 bytes, max name = 56 bytes
        char const_name[64] = "SOLVER_";
        const size_t prefix_len = 7;
        const size_t max_name_len = sizeof(const_name) - prefix_len - 1;
        size_t name_len = strlen(solver_names[i]);

        // Skip solver names that are too long (would cause truncation)
        if (name_len > max_name_len) {
            continue;
        }

        for (size_t j = 0; j < name_len; j++) {
            char c = solver_names[i][j];
            if (c >= 'a' && c <= 'z') {
                const_name[prefix_len + j] = c - 'a' + 'A';  // to uppercase
            } else {
                const_name[prefix_len + j] = c;
            }
        }
        const_name[prefix_len + name_len] = '\0';
        if (PyModule_AddStringConstant(m, const_name, solver_names[i]) < 0) {
            Py_DECREF(m);
            return NULL;
        }
    }

    // Add output field type constants (these are defined in simulation_api.h enum)
    if (PyModule_AddIntConstant(m, "OUTPUT_PRESSURE", OUTPUT_PRESSURE) < 0 ||
        PyModule_AddIntConstant(m, "OUTPUT_VELOCITY", OUTPUT_VELOCITY) < 0 ||
        PyModule_AddIntConstant(m, "OUTPUT_FULL_FIELD", OUTPUT_FULL_FIELD) < 0 ||
        PyModule_AddIntConstant(m, "OUTPUT_CSV_TIMESERIES", OUTPUT_CSV_TIMESERIES) < 0 ||
        PyModule_AddIntConstant(m, "OUTPUT_CSV_CENTERLINE", OUTPUT_CSV_CENTERLINE) < 0 ||
        PyModule_AddIntConstant(m, "OUTPUT_CSV_STATISTICS", OUTPUT_CSV_STATISTICS) < 0) {
        Py_DECREF(m);
        return NULL;
    }

    return m;
}
