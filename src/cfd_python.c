// Py_LIMITED_API should be defined via build system (CMake) before including Python.h
// for stable ABI support. The CMake option CFD_USE_STABLE_ABI controls this.
// When enabled, it targets Python 3.8+ stable ABI (0x03080000) for binary compatibility
// across Python versions. Do NOT define it here unconditionally as it requires linking
// against python3.lib which may not be available in all environments.

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdio.h>
#include <stdlib.h>

// Include CFD library headers (v0.1.5+ API)
#include "cfd/core/grid.h"
#include "cfd/core/cfd_status.h"
#include "cfd/core/derived_fields.h"
#include "cfd/core/cpu_features.h"
#include "cfd/solvers/navier_stokes_solver.h"
#include "cfd/api/simulation_api.h"
#include "cfd/io/vtk_output.h"
#include "cfd/io/csv_output.h"
#include "cfd/boundary/boundary_conditions.h"

// Module-level solver registry (context-bound)
static ns_solver_registry_t* g_registry = NULL;

/*
 * Helper to raise CFD errors as Python exceptions
 */
static PyObject* raise_cfd_error(cfd_status_t status, const char* context) {
    const char* error_msg = cfd_get_last_error();
    const char* status_str = cfd_get_error_string(status);

    if (error_msg && error_msg[0] != '\0') {
        PyErr_Format(PyExc_RuntimeError, "%s: %s (%s)", context, error_msg, status_str);
    } else {
        PyErr_Format(PyExc_RuntimeError, "%s: %s", context, status_str);
    }

    cfd_clear_error();
    return NULL;
}

/*
 * List available solvers
 */
static PyObject* list_solvers(PyObject* self, PyObject* args) {
    (void)self;
    (void)args;

    if (g_registry == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "Solver registry not initialized");
        return NULL;
    }

    const char* names[32];
    int count = cfd_registry_list(g_registry, names, 32);

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

    if (g_registry == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "Solver registry not initialized");
        return NULL;
    }

    int available = cfd_registry_has(g_registry, solver_type);
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

    if (g_registry == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "Solver registry not initialized");
        return NULL;
    }

    // Create a temporary solver to get its info
    ns_solver_t* solver = cfd_solver_create(g_registry, solver_type);
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

    APPEND_CAP(caps, NS_SOLVER_CAP_INCOMPRESSIBLE, "incompressible");
    APPEND_CAP(caps, NS_SOLVER_CAP_COMPRESSIBLE, "compressible");
    APPEND_CAP(caps, NS_SOLVER_CAP_STEADY_STATE, "steady_state");
    APPEND_CAP(caps, NS_SOLVER_CAP_TRANSIENT, "transient");
    APPEND_CAP(caps, NS_SOLVER_CAP_SIMD, "simd");
    APPEND_CAP(caps, NS_SOLVER_CAP_PARALLEL, "parallel");
    APPEND_CAP(caps, NS_SOLVER_CAP_GPU, "gpu");

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

    simulation_data* sim_data;
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

    // Compute velocity magnitude using derived_fields
    flow_field* field = sim_data->field;
    derived_fields* derived = derived_fields_create(field->nx, field->ny);
    if (derived == NULL) {
        free_simulation(sim_data);
        PyErr_SetString(PyExc_MemoryError, "Failed to create derived fields");
        return NULL;
    }

    derived_fields_compute_velocity_magnitude(derived, field);

    PyObject* result = PyList_New(0);
    if (result == NULL) {
        derived_fields_destroy(derived);
        free_simulation(sim_data);
        return NULL;
    }

    if (derived->velocity_magnitude != NULL) {
        size_t size = field->nx * field->ny;
        for (size_t i = 0; i < size; i++) {
            PyObject* val = PyFloat_FromDouble(derived->velocity_magnitude[i]);
            if (val == NULL || PyList_Append(result, val) < 0) {
                Py_XDECREF(val);
                Py_DECREF(result);
                derived_fields_destroy(derived);
                free_simulation(sim_data);
                return NULL;
            }
            Py_DECREF(val);
        }
    }

    derived_fields_destroy(derived);
    free_simulation(sim_data);
    return result;
}

/*
 * Create a simple grid function
 */
static PyObject* create_grid(PyObject* self, PyObject* args) {
    (void)self;
    Py_ssize_t nx_signed, ny_signed;
    double xmin, xmax, ymin, ymax;

    if (!PyArg_ParseTuple(args, "nndddd", &nx_signed, &ny_signed, &xmin, &xmax, &ymin, &ymax)) {
        return NULL;
    }

    // Validate dimensions before calling C library
    if (nx_signed < 2) {
        PyErr_SetString(PyExc_ValueError, "nx must be at least 2");
        return NULL;
    }
    if (ny_signed < 2) {
        PyErr_SetString(PyExc_ValueError, "ny must be at least 2");
        return NULL;
    }
    if (xmax <= xmin) {
        PyErr_SetString(PyExc_ValueError, "xmax must be greater than xmin");
        return NULL;
    }
    if (ymax <= ymin) {
        PyErr_SetString(PyExc_ValueError, "ymax must be greater than ymin");
        return NULL;
    }

    size_t nx = (size_t)nx_signed;
    size_t ny = (size_t)ny_signed;

    grid* g = grid_create(nx, ny, xmin, xmax, ymin, ymax);
    if (g == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to create grid");
        return NULL;
    }

    grid_initialize_uniform(g);

    // Return grid information as a dictionary
    PyObject* grid_dict = PyDict_New();
    if (grid_dict == NULL) {
        grid_destroy(g);
        return NULL;
    }

    // Helper macro to add values to dict with proper refcount
    #define ADD_TO_DICT(dict, key, py_val) do { \
        PyObject* tmp = (py_val); \
        if (tmp == NULL) { Py_DECREF(dict); grid_destroy(g); return NULL; } \
        PyDict_SetItemString(dict, key, tmp); \
        Py_DECREF(tmp); \
    } while(0)

    ADD_TO_DICT(grid_dict, "nx", PyLong_FromSize_t(g->nx));
    ADD_TO_DICT(grid_dict, "ny", PyLong_FromSize_t(g->ny));
    ADD_TO_DICT(grid_dict, "xmin", PyFloat_FromDouble(g->xmin));
    ADD_TO_DICT(grid_dict, "xmax", PyFloat_FromDouble(g->xmax));
    ADD_TO_DICT(grid_dict, "ymin", PyFloat_FromDouble(g->ymin));
    ADD_TO_DICT(grid_dict, "ymax", PyFloat_FromDouble(g->ymax));

    #undef ADD_TO_DICT

    // Create coordinate lists
    PyObject* x_list = PyList_New(0);
    PyObject* y_list = PyList_New(0);
    if (x_list == NULL || y_list == NULL) {
        Py_XDECREF(x_list);
        Py_XDECREF(y_list);
        Py_DECREF(grid_dict);
        grid_destroy(g);
        return NULL;
    }

    for (size_t i = 0; i < g->nx; i++) {
        PyObject* val = PyFloat_FromDouble(g->x[i]);
        if (val == NULL || PyList_Append(x_list, val) < 0) {
            Py_XDECREF(val);
            Py_DECREF(x_list);
            Py_DECREF(y_list);
            Py_DECREF(grid_dict);
            grid_destroy(g);
            return NULL;
        }
        Py_DECREF(val);
    }

    for (size_t i = 0; i < g->ny; i++) {
        PyObject* val = PyFloat_FromDouble(g->y[i]);
        if (val == NULL || PyList_Append(y_list, val) < 0) {
            Py_XDECREF(val);
            Py_DECREF(x_list);
            Py_DECREF(y_list);
            Py_DECREF(grid_dict);
            grid_destroy(g);
            return NULL;
        }
        Py_DECREF(val);
    }

    PyDict_SetItemString(grid_dict, "x_coords", x_list);
    PyDict_SetItemString(grid_dict, "y_coords", y_list);
    Py_DECREF(x_list);
    Py_DECREF(y_list);

    grid_destroy(g);
    return grid_dict;
}

/*
 * Get default solver parameters
 */
static PyObject* get_default_solver_params(PyObject* self, PyObject* args) {
    (void)self;
    (void)args;
    ns_solver_params_t params = ns_solver_params_default();

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

    simulation_data* sim_data;
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

    // Compute velocity magnitude using derived_fields
    flow_field* field = sim_data->field;
    derived_fields* derived = derived_fields_create(field->nx, field->ny);
    if (derived != NULL) {
        derived_fields_compute_velocity_magnitude(derived, field);

        if (derived->velocity_magnitude != NULL) {
            size_t size = field->nx * field->ny;
            PyObject* vel_list = PyList_New(0);
            if (vel_list == NULL) {
                derived_fields_destroy(derived);
                Py_DECREF(results);
                free_simulation(sim_data);
                return NULL;
            }
            for (size_t i = 0; i < size; i++) {
                PyObject* val = PyFloat_FromDouble(derived->velocity_magnitude[i]);
                if (val == NULL || PyList_Append(vel_list, val) < 0) {
                    Py_XDECREF(val);
                    Py_DECREF(vel_list);
                    derived_fields_destroy(derived);
                    Py_DECREF(results);
                    free_simulation(sim_data);
                    return NULL;
                }
                Py_DECREF(val);
            }
            PyDict_SetItemString(results, "velocity_magnitude", vel_list);
            Py_DECREF(vel_list);
        }
        derived_fields_destroy(derived);
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
    ns_solver_t* solver = simulation_get_solver(sim_data);
    if (solver) {
        ADD_TO_DICT(results, "solver_name", PyUnicode_FromString(solver->name));
        ADD_TO_DICT(results, "solver_description", PyUnicode_FromString(solver->description));
    }

    // Add solver statistics
    const ns_solver_stats_t* stats = simulation_get_stats(sim_data);
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

    // Note: This function now requires a simulation_data context
    // For now, we'll warn that this is a no-op without a simulation context
    PyErr_WarnEx(PyExc_DeprecationWarning,
                 "set_output_dir() without simulation context is deprecated. "
                 "Use simulation_data.output_base_dir instead.", 1);
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
    flow_field* field = flow_field_create(nx, ny);
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

    ns_solver_params_t params = ns_solver_params_default();
    params.dt = dt;

    ns_solver_stats_t stats = ns_solver_stats_default();
    stats.iterations = iterations;

    // New API: write_csv_timeseries takes derived_fields* (can be NULL)
    write_csv_timeseries(filename, step, time, field, NULL, &params, &stats, nx, ny, create_new);

    flow_field_destroy(field);
    Py_RETURN_NONE;
}

/*
 * Get last CFD error
 */
static PyObject* get_last_error(PyObject* self, PyObject* args) {
    (void)self;
    (void)args;

    const char* error = cfd_get_last_error();
    if (error && error[0] != '\0') {
        return PyUnicode_FromString(error);
    }
    Py_RETURN_NONE;
}

/*
 * Get last CFD status code
 */
static PyObject* get_last_status(PyObject* self, PyObject* args) {
    (void)self;
    (void)args;

    cfd_status_t status = cfd_get_last_status();
    return PyLong_FromLong((long)status);
}

/*
 * Clear CFD error state
 */
static PyObject* clear_error(PyObject* self, PyObject* args) {
    (void)self;
    (void)args;

    cfd_clear_error();
    Py_RETURN_NONE;
}

/*
 * Get error string for status code
 */
static PyObject* get_error_string(PyObject* self, PyObject* args) {
    (void)self;
    int status;

    if (!PyArg_ParseTuple(args, "i", &status)) {
        return NULL;
    }

    const char* str = cfd_get_error_string((cfd_status_t)status);
    return PyUnicode_FromString(str);
}

/* ============================================================================
 * BOUNDARY CONDITIONS API
 * ============================================================================ */

/*
 * Get current BC backend
 */
static PyObject* bc_get_backend_py(PyObject* self, PyObject* args) {
    (void)self;
    (void)args;
    return PyLong_FromLong((long)bc_get_backend());
}

/*
 * Get BC backend name as string
 */
static PyObject* bc_get_backend_name_py(PyObject* self, PyObject* args) {
    (void)self;
    (void)args;
    return PyUnicode_FromString(bc_get_backend_name());
}

/*
 * Set BC backend
 */
static PyObject* bc_set_backend_py(PyObject* self, PyObject* args) {
    (void)self;
    int backend;

    if (!PyArg_ParseTuple(args, "i", &backend)) {
        return NULL;
    }

    bool success = bc_set_backend((bc_backend_t)backend);
    return PyBool_FromLong(success);
}

/*
 * Check if BC backend is available
 */
static PyObject* bc_backend_available_py(PyObject* self, PyObject* args) {
    (void)self;
    int backend;

    if (!PyArg_ParseTuple(args, "i", &backend)) {
        return NULL;
    }

    bool available = bc_backend_available((bc_backend_t)backend);
    return PyBool_FromLong(available);
}

/*
 * ========================================
 * Solver Backend Availability API (v0.1.6)
 * ========================================
 */

/*
 * Check if a solver backend is available at runtime
 */
static PyObject* backend_is_available_py(PyObject* self, PyObject* args) {
    (void)self;
    int backend;

    if (!PyArg_ParseTuple(args, "i", &backend)) {
        return NULL;
    }

    int available = cfd_backend_is_available((ns_solver_backend_t)backend);
    return PyBool_FromLong(available);
}

/*
 * Get human-readable name for a solver backend
 */
static PyObject* backend_get_name_py(PyObject* self, PyObject* args) {
    (void)self;
    int backend;

    if (!PyArg_ParseTuple(args, "i", &backend)) {
        return NULL;
    }

    const char* name = cfd_backend_get_name((ns_solver_backend_t)backend);
    if (name == NULL) {
        Py_RETURN_NONE;
    }
    return PyUnicode_FromString(name);
}

/*
 * Get list of solvers for a specific backend
 */
static PyObject* list_solvers_by_backend_py(PyObject* self, PyObject* args) {
    (void)self;
    int backend;

    if (!PyArg_ParseTuple(args, "i", &backend)) {
        return NULL;
    }

    if (g_registry == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "Solver registry not initialized");
        return NULL;
    }

    // First, get the count
    int count = cfd_registry_list_by_backend(g_registry, (ns_solver_backend_t)backend, NULL, 0);
    if (count <= 0) {
        return PyList_New(0);  // Return empty list
    }

    // Allocate array for names
    const char** names = (const char**)malloc(count * sizeof(const char*));
    if (names == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate names array");
        return NULL;
    }

    // Get the actual names
    int actual_count = cfd_registry_list_by_backend(g_registry, (ns_solver_backend_t)backend, names, count);

    // Build Python list
    PyObject* result = PyList_New(actual_count);
    if (result == NULL) {
        free(names);
        return NULL;
    }

    for (int i = 0; i < actual_count; i++) {
        PyObject* name = PyUnicode_FromString(names[i]);
        if (name == NULL) {
            Py_DECREF(result);
            free(names);
            return NULL;
        }
        PyList_SetItem(result, i, name);  // Steals reference
    }

    free(names);
    return result;
}

/*
 * Get list of all available backends
 */
static PyObject* get_available_backends_py(PyObject* self, PyObject* args) {
    (void)self;
    (void)args;

    PyObject* result = PyList_New(0);
    if (result == NULL) {
        return NULL;
    }

    // Check each backend
    ns_solver_backend_t backends[] = {
        NS_SOLVER_BACKEND_SCALAR,
        NS_SOLVER_BACKEND_SIMD,
        NS_SOLVER_BACKEND_OMP,
        NS_SOLVER_BACKEND_CUDA
    };
    int num_backends = sizeof(backends) / sizeof(backends[0]);

    for (int i = 0; i < num_backends; i++) {
        if (cfd_backend_is_available(backends[i])) {
            const char* name = cfd_backend_get_name(backends[i]);
            if (name != NULL) {
                PyObject* name_obj = PyUnicode_FromString(name);
                if (name_obj == NULL) {
                    Py_DECREF(result);
                    return NULL;
                }
                if (PyList_Append(result, name_obj) < 0) {
                    Py_DECREF(name_obj);
                    Py_DECREF(result);
                    return NULL;
                }
                Py_DECREF(name_obj);
            }
        }
    }

    return result;
}

// ============================================================================
// CPU Features API (Phase 6)
// ============================================================================

/*
 * Get the detected SIMD architecture
 * Returns: int (SIMD_NONE=0, SIMD_AVX2=1, SIMD_NEON=2)
 */
static PyObject* get_simd_arch_py(PyObject* self, PyObject* args) {
    (void)self;
    (void)args;

    cfd_simd_arch_t arch = cfd_detect_simd_arch();
    return PyLong_FromLong((long)arch);
}

/*
 * Get the name of the detected SIMD architecture
 * Returns: str ("avx2", "neon", or "none")
 */
static PyObject* get_simd_name_py(PyObject* self, PyObject* args) {
    (void)self;
    (void)args;

    const char* name = cfd_get_simd_name();
    return PyUnicode_FromString(name);
}

/*
 * Check if AVX2 is available
 * Returns: bool
 */
static PyObject* has_avx2_py(PyObject* self, PyObject* args) {
    (void)self;
    (void)args;

    bool available = cfd_has_avx2();
    return PyBool_FromLong(available);
}

/*
 * Check if ARM NEON is available
 * Returns: bool
 */
static PyObject* has_neon_py(PyObject* self, PyObject* args) {
    (void)self;
    (void)args;

    bool available = cfd_has_neon();
    return PyBool_FromLong(available);
}

/*
 * Check if any SIMD is available (AVX2 or NEON)
 * Returns: bool
 */
static PyObject* has_simd_py(PyObject* self, PyObject* args) {
    (void)self;
    (void)args;

    bool available = cfd_has_simd();
    return PyBool_FromLong(available);
}

// ============================================================================
// Grid Initialization Variants (Phase 6)
// ============================================================================

/*
 * Create a grid with stretched (non-uniform) spacing
 * Args: nx, ny, xmin, xmax, ymin, ymax, beta
 * Returns: dict with grid information
 */
static PyObject* create_grid_stretched_py(PyObject* self, PyObject* args) {
    (void)self;

    long nx_signed, ny_signed;
    double xmin, xmax, ymin, ymax, beta;

    if (!PyArg_ParseTuple(args, "llddddd", &nx_signed, &ny_signed,
                          &xmin, &xmax, &ymin, &ymax, &beta)) {
        return NULL;
    }

    if (nx_signed <= 0 || ny_signed <= 0) {
        PyErr_SetString(PyExc_ValueError, "Grid dimensions must be positive");
        return NULL;
    }
    if (xmax <= xmin) {
        PyErr_SetString(PyExc_ValueError, "xmax must be greater than xmin");
        return NULL;
    }
    if (ymax <= ymin) {
        PyErr_SetString(PyExc_ValueError, "ymax must be greater than ymin");
        return NULL;
    }
    if (beta <= 0.0) {
        PyErr_SetString(PyExc_ValueError, "beta must be positive");
        return NULL;
    }

    size_t nx = (size_t)nx_signed;
    size_t ny = (size_t)ny_signed;

    grid* g = grid_create(nx, ny, xmin, xmax, ymin, ymax);
    if (g == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to create grid");
        return NULL;
    }

    grid_initialize_stretched(g, beta);

    // Return grid information as a dictionary
    PyObject* grid_dict = PyDict_New();
    if (grid_dict == NULL) {
        grid_destroy(g);
        return NULL;
    }

    // Helper macro to add values to dict with proper refcount and error handling
    #define ADD_TO_DICT_STRETCHED(dict, key, py_val) do { \
        PyObject* tmp = (py_val); \
        if (tmp == NULL) { Py_DECREF(dict); grid_destroy(g); return NULL; } \
        if (PyDict_SetItemString(dict, key, tmp) < 0) { \
            Py_DECREF(tmp); Py_DECREF(dict); grid_destroy(g); return NULL; \
        } \
        Py_DECREF(tmp); \
    } while(0)

    ADD_TO_DICT_STRETCHED(grid_dict, "nx", PyLong_FromSize_t(g->nx));
    ADD_TO_DICT_STRETCHED(grid_dict, "ny", PyLong_FromSize_t(g->ny));
    ADD_TO_DICT_STRETCHED(grid_dict, "xmin", PyFloat_FromDouble(g->xmin));
    ADD_TO_DICT_STRETCHED(grid_dict, "xmax", PyFloat_FromDouble(g->xmax));
    ADD_TO_DICT_STRETCHED(grid_dict, "ymin", PyFloat_FromDouble(g->ymin));
    ADD_TO_DICT_STRETCHED(grid_dict, "ymax", PyFloat_FromDouble(g->ymax));
    ADD_TO_DICT_STRETCHED(grid_dict, "beta", PyFloat_FromDouble(beta));

    #undef ADD_TO_DICT_STRETCHED

    // Create coordinate lists
    PyObject* x_list = PyList_New((Py_ssize_t)g->nx);
    PyObject* y_list = PyList_New((Py_ssize_t)g->ny);
    if (x_list == NULL || y_list == NULL) {
        Py_XDECREF(x_list);
        Py_XDECREF(y_list);
        Py_DECREF(grid_dict);
        grid_destroy(g);
        return NULL;
    }

    for (size_t i = 0; i < g->nx; i++) {
        PyObject* val = PyFloat_FromDouble(g->x[i]);
        if (val == NULL) {
            Py_DECREF(x_list);
            Py_DECREF(y_list);
            Py_DECREF(grid_dict);
            grid_destroy(g);
            return NULL;
        }
        if (PyList_SetItem(x_list, (Py_ssize_t)i, val) < 0) {  // steals reference
            Py_DECREF(x_list);
            Py_DECREF(y_list);
            Py_DECREF(grid_dict);
            grid_destroy(g);
            return NULL;
        }
    }

    for (size_t i = 0; i < g->ny; i++) {
        PyObject* val = PyFloat_FromDouble(g->y[i]);
        if (val == NULL) {
            Py_DECREF(x_list);
            Py_DECREF(y_list);
            Py_DECREF(grid_dict);
            grid_destroy(g);
            return NULL;
        }
        if (PyList_SetItem(y_list, (Py_ssize_t)i, val) < 0) {  // steals reference
            Py_DECREF(x_list);
            Py_DECREF(y_list);
            Py_DECREF(grid_dict);
            grid_destroy(g);
            return NULL;
        }
    }

    if (PyDict_SetItemString(grid_dict, "x", x_list) < 0 ||
        PyDict_SetItemString(grid_dict, "y", y_list) < 0) {
        Py_DECREF(x_list);
        Py_DECREF(y_list);
        Py_DECREF(grid_dict);
        grid_destroy(g);
        return NULL;
    }
    Py_DECREF(x_list);
    Py_DECREF(y_list);

    grid_destroy(g);
    return grid_dict;
}

/*
 * Apply boundary conditions to scalar field
 */
static PyObject* bc_apply_scalar_py(PyObject* self, PyObject* args, PyObject* kwds) {
    (void)self;
    static char* kwlist[] = {"field", "nx", "ny", "bc_type", NULL};
    PyObject* field_list;
    size_t nx, ny;
    int bc_type;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "Onni", kwlist,
                                     &field_list, &nx, &ny, &bc_type)) {
        return NULL;
    }

    if (!PyList_Check(field_list)) {
        PyErr_SetString(PyExc_TypeError, "field must be a list");
        return NULL;
    }

    size_t size = nx * ny;
    if ((size_t)PyList_Size(field_list) != size) {
        PyErr_Format(PyExc_ValueError, "field size (%zd) must match nx*ny (%zu)",
                     PyList_Size(field_list), size);
        return NULL;
    }

    // Convert list to C array
    double* field = (double*)malloc(size * sizeof(double));
    if (field == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate field array");
        return NULL;
    }

    for (size_t i = 0; i < size; i++) {
        PyObject* item = PyList_GetItem(field_list, i);
        field[i] = PyFloat_AsDouble(item);
        if (PyErr_Occurred()) {
            free(field);
            return NULL;
        }
    }

    // Apply BC
    cfd_status_t status = bc_apply_scalar(field, nx, ny, (bc_type_t)bc_type);
    if (status != CFD_SUCCESS) {
        free(field);
        return raise_cfd_error(status, "bc_apply_scalar");
    }

    // Copy back to list
    for (size_t i = 0; i < size; i++) {
        PyObject* val = PyFloat_FromDouble(field[i]);
        if (val == NULL) {
            free(field);
            return NULL;
        }
        if (PyList_SetItem(field_list, i, val) < 0) {
            free(field);
            return NULL;
        }
    }

    free(field);
    Py_RETURN_NONE;
}

/*
 * Apply boundary conditions to velocity fields
 */
static PyObject* bc_apply_velocity_py(PyObject* self, PyObject* args, PyObject* kwds) {
    (void)self;
    static char* kwlist[] = {"u", "v", "nx", "ny", "bc_type", NULL};
    PyObject* u_list;
    PyObject* v_list;
    size_t nx, ny;
    int bc_type;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOnni", kwlist,
                                     &u_list, &v_list, &nx, &ny, &bc_type)) {
        return NULL;
    }

    if (!PyList_Check(u_list) || !PyList_Check(v_list)) {
        PyErr_SetString(PyExc_TypeError, "u and v must be lists");
        return NULL;
    }

    size_t size = nx * ny;
    if ((size_t)PyList_Size(u_list) != size || (size_t)PyList_Size(v_list) != size) {
        PyErr_SetString(PyExc_ValueError, "u and v sizes must match nx*ny");
        return NULL;
    }

    // Convert lists to C arrays
    double* u = (double*)malloc(size * sizeof(double));
    double* v = (double*)malloc(size * sizeof(double));
    if (u == NULL || v == NULL) {
        free(u);
        free(v);
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate velocity arrays");
        return NULL;
    }

    for (size_t i = 0; i < size; i++) {
        u[i] = PyFloat_AsDouble(PyList_GetItem(u_list, i));
        v[i] = PyFloat_AsDouble(PyList_GetItem(v_list, i));
        if (PyErr_Occurred()) {
            free(u);
            free(v);
            return NULL;
        }
    }

    // Apply BC
    cfd_status_t status = bc_apply_velocity(u, v, nx, ny, (bc_type_t)bc_type);
    if (status != CFD_SUCCESS) {
        free(u);
        free(v);
        return raise_cfd_error(status, "bc_apply_velocity");
    }

    // Copy back to lists
    for (size_t i = 0; i < size; i++) {
        PyObject* u_val = PyFloat_FromDouble(u[i]);
        PyObject* v_val = PyFloat_FromDouble(v[i]);
        if (u_val == NULL || v_val == NULL) {
            Py_XDECREF(u_val);
            Py_XDECREF(v_val);
            free(u);
            free(v);
            return NULL;
        }
        PyList_SetItem(u_list, i, u_val);
        PyList_SetItem(v_list, i, v_val);
    }

    free(u);
    free(v);
    Py_RETURN_NONE;
}

/*
 * Apply Dirichlet boundary conditions to scalar field
 */
static PyObject* bc_apply_dirichlet_scalar_py(PyObject* self, PyObject* args, PyObject* kwds) {
    (void)self;
    static char* kwlist[] = {"field", "nx", "ny", "left", "right", "bottom", "top", NULL};
    PyObject* field_list;
    size_t nx, ny;
    double left, right, bottom, top;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "Onndddd", kwlist,
                                     &field_list, &nx, &ny, &left, &right, &bottom, &top)) {
        return NULL;
    }

    if (!PyList_Check(field_list)) {
        PyErr_SetString(PyExc_TypeError, "field must be a list");
        return NULL;
    }

    size_t size = nx * ny;
    if ((size_t)PyList_Size(field_list) != size) {
        PyErr_Format(PyExc_ValueError, "field size (%zd) must match nx*ny (%zu)",
                     PyList_Size(field_list), size);
        return NULL;
    }

    // Convert list to C array
    double* field = (double*)malloc(size * sizeof(double));
    if (field == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate field array");
        return NULL;
    }

    for (size_t i = 0; i < size; i++) {
        field[i] = PyFloat_AsDouble(PyList_GetItem(field_list, i));
        if (PyErr_Occurred()) {
            free(field);
            return NULL;
        }
    }

    // Apply Dirichlet BC
    bc_dirichlet_values_t values = {.left = left, .right = right, .bottom = bottom, .top = top};
    cfd_status_t status = bc_apply_dirichlet_scalar(field, nx, ny, &values);
    if (status != CFD_SUCCESS) {
        free(field);
        return raise_cfd_error(status, "bc_apply_dirichlet_scalar");
    }

    // Copy back to list
    for (size_t i = 0; i < size; i++) {
        PyObject* val = PyFloat_FromDouble(field[i]);
        if (val == NULL) {
            free(field);
            return NULL;
        }
        PyList_SetItem(field_list, i, val);
    }

    free(field);
    Py_RETURN_NONE;
}

/*
 * Apply no-slip boundary conditions to velocity fields
 */
static PyObject* bc_apply_noslip_py(PyObject* self, PyObject* args, PyObject* kwds) {
    (void)self;
    static char* kwlist[] = {"u", "v", "nx", "ny", NULL};
    PyObject* u_list;
    PyObject* v_list;
    size_t nx, ny;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOnn", kwlist,
                                     &u_list, &v_list, &nx, &ny)) {
        return NULL;
    }

    if (!PyList_Check(u_list) || !PyList_Check(v_list)) {
        PyErr_SetString(PyExc_TypeError, "u and v must be lists");
        return NULL;
    }

    size_t size = nx * ny;
    if ((size_t)PyList_Size(u_list) != size || (size_t)PyList_Size(v_list) != size) {
        PyErr_SetString(PyExc_ValueError, "u and v sizes must match nx*ny");
        return NULL;
    }

    // Convert lists to C arrays
    double* u = (double*)malloc(size * sizeof(double));
    double* v = (double*)malloc(size * sizeof(double));
    if (u == NULL || v == NULL) {
        free(u);
        free(v);
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate velocity arrays");
        return NULL;
    }

    for (size_t i = 0; i < size; i++) {
        u[i] = PyFloat_AsDouble(PyList_GetItem(u_list, i));
        v[i] = PyFloat_AsDouble(PyList_GetItem(v_list, i));
        if (PyErr_Occurred()) {
            free(u);
            free(v);
            return NULL;
        }
    }

    // Apply no-slip BC
    cfd_status_t status = bc_apply_noslip(u, v, nx, ny);
    if (status != CFD_SUCCESS) {
        free(u);
        free(v);
        return raise_cfd_error(status, "bc_apply_noslip");
    }

    // Copy back to lists
    for (size_t i = 0; i < size; i++) {
        PyObject* u_val = PyFloat_FromDouble(u[i]);
        PyObject* v_val = PyFloat_FromDouble(v[i]);
        if (u_val == NULL || v_val == NULL) {
            Py_XDECREF(u_val);
            Py_XDECREF(v_val);
            free(u);
            free(v);
            return NULL;
        }
        PyList_SetItem(u_list, i, u_val);
        PyList_SetItem(v_list, i, v_val);
    }

    free(u);
    free(v);
    Py_RETURN_NONE;
}

/*
 * Apply inlet boundary conditions
 */
static PyObject* bc_apply_inlet_uniform_py(PyObject* self, PyObject* args, PyObject* kwds) {
    (void)self;
    static char* kwlist[] = {"u", "v", "nx", "ny", "u_inlet", "v_inlet", "edge", NULL};
    PyObject* u_list;
    PyObject* v_list;
    size_t nx, ny;
    double u_inlet, v_inlet;
    int edge = BC_EDGE_LEFT;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOnndd|i", kwlist,
                                     &u_list, &v_list, &nx, &ny, &u_inlet, &v_inlet, &edge)) {
        return NULL;
    }

    if (!PyList_Check(u_list) || !PyList_Check(v_list)) {
        PyErr_SetString(PyExc_TypeError, "u and v must be lists");
        return NULL;
    }

    size_t size = nx * ny;
    if ((size_t)PyList_Size(u_list) != size || (size_t)PyList_Size(v_list) != size) {
        PyErr_SetString(PyExc_ValueError, "u and v sizes must match nx*ny");
        return NULL;
    }

    // Convert lists to C arrays
    double* u = (double*)malloc(size * sizeof(double));
    double* v = (double*)malloc(size * sizeof(double));
    if (u == NULL || v == NULL) {
        free(u);
        free(v);
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate velocity arrays");
        return NULL;
    }

    for (size_t i = 0; i < size; i++) {
        u[i] = PyFloat_AsDouble(PyList_GetItem(u_list, i));
        v[i] = PyFloat_AsDouble(PyList_GetItem(v_list, i));
        if (PyErr_Occurred()) {
            free(u);
            free(v);
            return NULL;
        }
    }

    // Create inlet config and apply
    bc_inlet_config_t config = bc_inlet_config_uniform(u_inlet, v_inlet);
    bc_inlet_set_edge(&config, (bc_edge_t)edge);

    cfd_status_t status = bc_apply_inlet(u, v, nx, ny, &config);
    if (status != CFD_SUCCESS) {
        free(u);
        free(v);
        return raise_cfd_error(status, "bc_apply_inlet");
    }

    // Copy back to lists
    for (size_t i = 0; i < size; i++) {
        PyObject* u_val = PyFloat_FromDouble(u[i]);
        PyObject* v_val = PyFloat_FromDouble(v[i]);
        if (u_val == NULL || v_val == NULL) {
            Py_XDECREF(u_val);
            Py_XDECREF(v_val);
            free(u);
            free(v);
            return NULL;
        }
        PyList_SetItem(u_list, i, u_val);
        PyList_SetItem(v_list, i, v_val);
    }

    free(u);
    free(v);
    Py_RETURN_NONE;
}

/*
 * Apply parabolic inlet boundary conditions
 */
static PyObject* bc_apply_inlet_parabolic_py(PyObject* self, PyObject* args, PyObject* kwds) {
    (void)self;
    static char* kwlist[] = {"u", "v", "nx", "ny", "max_velocity", "edge", NULL};
    PyObject* u_list;
    PyObject* v_list;
    size_t nx, ny;
    double max_velocity;
    int edge = BC_EDGE_LEFT;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOnnd|i", kwlist,
                                     &u_list, &v_list, &nx, &ny, &max_velocity, &edge)) {
        return NULL;
    }

    if (!PyList_Check(u_list) || !PyList_Check(v_list)) {
        PyErr_SetString(PyExc_TypeError, "u and v must be lists");
        return NULL;
    }

    size_t size = nx * ny;
    if ((size_t)PyList_Size(u_list) != size || (size_t)PyList_Size(v_list) != size) {
        PyErr_SetString(PyExc_ValueError, "u and v sizes must match nx*ny");
        return NULL;
    }

    // Convert lists to C arrays
    double* u = (double*)malloc(size * sizeof(double));
    double* v = (double*)malloc(size * sizeof(double));
    if (u == NULL || v == NULL) {
        free(u);
        free(v);
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate velocity arrays");
        return NULL;
    }

    for (size_t i = 0; i < size; i++) {
        u[i] = PyFloat_AsDouble(PyList_GetItem(u_list, i));
        v[i] = PyFloat_AsDouble(PyList_GetItem(v_list, i));
        if (PyErr_Occurred()) {
            free(u);
            free(v);
            return NULL;
        }
    }

    // Create parabolic inlet config and apply
    bc_inlet_config_t config = bc_inlet_config_parabolic(max_velocity);
    bc_inlet_set_edge(&config, (bc_edge_t)edge);

    cfd_status_t status = bc_apply_inlet(u, v, nx, ny, &config);
    if (status != CFD_SUCCESS) {
        free(u);
        free(v);
        return raise_cfd_error(status, "bc_apply_inlet");
    }

    // Copy back to lists
    for (size_t i = 0; i < size; i++) {
        PyObject* u_val = PyFloat_FromDouble(u[i]);
        PyObject* v_val = PyFloat_FromDouble(v[i]);
        if (u_val == NULL || v_val == NULL) {
            Py_XDECREF(u_val);
            Py_XDECREF(v_val);
            free(u);
            free(v);
            return NULL;
        }
        PyList_SetItem(u_list, i, u_val);
        PyList_SetItem(v_list, i, v_val);
    }

    free(u);
    free(v);
    Py_RETURN_NONE;
}

/*
 * Apply outlet (zero-gradient) boundary conditions to scalar field
 */
static PyObject* bc_apply_outlet_scalar_py(PyObject* self, PyObject* args, PyObject* kwds) {
    (void)self;
    static char* kwlist[] = {"field", "nx", "ny", "edge", NULL};
    PyObject* field_list;
    size_t nx, ny;
    int edge = BC_EDGE_RIGHT;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "Onn|i", kwlist,
                                     &field_list, &nx, &ny, &edge)) {
        return NULL;
    }

    if (!PyList_Check(field_list)) {
        PyErr_SetString(PyExc_TypeError, "field must be a list");
        return NULL;
    }

    size_t size = nx * ny;
    if ((size_t)PyList_Size(field_list) != size) {
        PyErr_Format(PyExc_ValueError, "field size (%zd) must match nx*ny (%zu)",
                     PyList_Size(field_list), size);
        return NULL;
    }

    // Convert list to C array
    double* field = (double*)malloc(size * sizeof(double));
    if (field == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate field array");
        return NULL;
    }

    for (size_t i = 0; i < size; i++) {
        field[i] = PyFloat_AsDouble(PyList_GetItem(field_list, i));
        if (PyErr_Occurred()) {
            free(field);
            return NULL;
        }
    }

    // Create outlet config and apply
    bc_outlet_config_t config = bc_outlet_config_zero_gradient();
    bc_outlet_set_edge(&config, (bc_edge_t)edge);

    cfd_status_t status = bc_apply_outlet_scalar(field, nx, ny, &config);
    if (status != CFD_SUCCESS) {
        free(field);
        return raise_cfd_error(status, "bc_apply_outlet_scalar");
    }

    // Copy back to list
    for (size_t i = 0; i < size; i++) {
        PyObject* val = PyFloat_FromDouble(field[i]);
        if (val == NULL) {
            free(field);
            return NULL;
        }
        PyList_SetItem(field_list, i, val);
    }

    free(field);
    Py_RETURN_NONE;
}

/*
 * Apply outlet boundary conditions to velocity fields
 */
static PyObject* bc_apply_outlet_velocity_py(PyObject* self, PyObject* args, PyObject* kwds) {
    (void)self;
    static char* kwlist[] = {"u", "v", "nx", "ny", "edge", NULL};
    PyObject* u_list;
    PyObject* v_list;
    size_t nx, ny;
    int edge = BC_EDGE_RIGHT;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOnn|i", kwlist,
                                     &u_list, &v_list, &nx, &ny, &edge)) {
        return NULL;
    }

    if (!PyList_Check(u_list) || !PyList_Check(v_list)) {
        PyErr_SetString(PyExc_TypeError, "u and v must be lists");
        return NULL;
    }

    size_t size = nx * ny;
    if ((size_t)PyList_Size(u_list) != size || (size_t)PyList_Size(v_list) != size) {
        PyErr_SetString(PyExc_ValueError, "u and v sizes must match nx*ny");
        return NULL;
    }

    // Convert lists to C arrays
    double* u = (double*)malloc(size * sizeof(double));
    double* v = (double*)malloc(size * sizeof(double));
    if (u == NULL || v == NULL) {
        free(u);
        free(v);
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate velocity arrays");
        return NULL;
    }

    for (size_t i = 0; i < size; i++) {
        u[i] = PyFloat_AsDouble(PyList_GetItem(u_list, i));
        v[i] = PyFloat_AsDouble(PyList_GetItem(v_list, i));
        if (PyErr_Occurred()) {
            free(u);
            free(v);
            return NULL;
        }
    }

    // Create outlet config and apply
    bc_outlet_config_t config = bc_outlet_config_zero_gradient();
    bc_outlet_set_edge(&config, (bc_edge_t)edge);

    cfd_status_t status = bc_apply_outlet_velocity(u, v, nx, ny, &config);
    if (status != CFD_SUCCESS) {
        free(u);
        free(v);
        return raise_cfd_error(status, "bc_apply_outlet_velocity");
    }

    // Copy back to lists
    for (size_t i = 0; i < size; i++) {
        PyObject* u_val = PyFloat_FromDouble(u[i]);
        PyObject* v_val = PyFloat_FromDouble(v[i]);
        if (u_val == NULL || v_val == NULL) {
            Py_XDECREF(u_val);
            Py_XDECREF(v_val);
            free(u);
            free(v);
            return NULL;
        }
        PyList_SetItem(u_list, i, u_val);
        PyList_SetItem(v_list, i, v_val);
    }

    free(u);
    free(v);
    Py_RETURN_NONE;
}

//=============================================================================
// DERIVED FIELDS API (Phase 3)
//=============================================================================

/*
 * Calculate field statistics (min, max, avg, sum)
 */
static PyObject* calculate_field_stats_py(PyObject* self, PyObject* args) {
    (void)self;
    PyObject* data_list;

    if (!PyArg_ParseTuple(args, "O", &data_list)) {
        return NULL;
    }

    if (!PyList_Check(data_list)) {
        PyErr_SetString(PyExc_TypeError, "data must be a list");
        return NULL;
    }

    Py_ssize_t count = PyList_Size(data_list);
    if (count == 0) {
        PyErr_SetString(PyExc_ValueError, "data list cannot be empty");
        return NULL;
    }

    // Convert list to C array
    double* data = (double*)malloc((size_t)count * sizeof(double));
    if (data == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate data array");
        return NULL;
    }

    for (Py_ssize_t i = 0; i < count; i++) {
        PyObject* item = PyList_GetItem(data_list, i);
        data[i] = PyFloat_AsDouble(item);
        if (PyErr_Occurred()) {
            free(data);
            return NULL;
        }
    }

    // Calculate statistics
    field_stats stats = calculate_field_statistics(data, (size_t)count);
    free(data);

    // Return as dictionary
    PyObject* result = PyDict_New();
    if (result == NULL) {
        return NULL;
    }

    PyObject* min_val = PyFloat_FromDouble(stats.min_val);
    PyObject* max_val = PyFloat_FromDouble(stats.max_val);
    PyObject* avg_val = PyFloat_FromDouble(stats.avg_val);
    PyObject* sum_val = PyFloat_FromDouble(stats.sum_val);

    if (min_val == NULL || max_val == NULL || avg_val == NULL || sum_val == NULL) {
        Py_XDECREF(min_val);
        Py_XDECREF(max_val);
        Py_XDECREF(avg_val);
        Py_XDECREF(sum_val);
        Py_DECREF(result);
        return NULL;
    }

    if (PyDict_SetItemString(result, "min", min_val) < 0 ||
        PyDict_SetItemString(result, "max", max_val) < 0 ||
        PyDict_SetItemString(result, "avg", avg_val) < 0 ||
        PyDict_SetItemString(result, "sum", sum_val) < 0) {
        Py_DECREF(min_val);
        Py_DECREF(max_val);
        Py_DECREF(avg_val);
        Py_DECREF(sum_val);
        Py_DECREF(result);
        return NULL;
    }

    Py_DECREF(min_val);
    Py_DECREF(max_val);
    Py_DECREF(avg_val);
    Py_DECREF(sum_val);

    return result;
}

/*
 * Compute velocity magnitude from u,v components
 */
static PyObject* compute_velocity_magnitude_py(PyObject* self, PyObject* args) {
    (void)self;
    PyObject* u_list;
    PyObject* v_list;
    size_t nx, ny;

    if (!PyArg_ParseTuple(args, "OOnn", &u_list, &v_list, &nx, &ny)) {
        return NULL;
    }

    if (!PyList_Check(u_list) || !PyList_Check(v_list)) {
        PyErr_SetString(PyExc_TypeError, "u and v must be lists");
        return NULL;
    }

    size_t size = nx * ny;
    if ((size_t)PyList_Size(u_list) != size || (size_t)PyList_Size(v_list) != size) {
        PyErr_Format(PyExc_ValueError,
                     "u and v size must match nx*ny (%zu), got %zd and %zd",
                     size, PyList_Size(u_list), PyList_Size(v_list));
        return NULL;
    }

    // Create a temporary flow_field structure
    flow_field* field = flow_field_create(nx, ny);
    if (field == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate flow field");
        return NULL;
    }

    // Copy u, v from lists
    for (size_t i = 0; i < size; i++) {
        field->u[i] = PyFloat_AsDouble(PyList_GetItem(u_list, i));
        field->v[i] = PyFloat_AsDouble(PyList_GetItem(v_list, i));
        if (PyErr_Occurred()) {
            flow_field_destroy(field);
            return NULL;
        }
    }

    // Create derived fields and compute velocity magnitude
    derived_fields* derived = derived_fields_create(nx, ny);
    if (derived == NULL) {
        flow_field_destroy(field);
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate derived fields");
        return NULL;
    }

    derived_fields_compute_velocity_magnitude(derived, field);

    // Create output list
    PyObject* result = PyList_New(size);
    if (result == NULL) {
        derived_fields_destroy(derived);
        flow_field_destroy(field);
        return NULL;
    }

    for (size_t i = 0; i < size; i++) {
        PyObject* val = PyFloat_FromDouble(derived->velocity_magnitude[i]);
        if (val == NULL) {
            Py_DECREF(result);
            derived_fields_destroy(derived);
            flow_field_destroy(field);
            return NULL;
        }
        PyList_SetItem(result, i, val);
    }

    derived_fields_destroy(derived);
    flow_field_destroy(field);

    return result;
}

/*
 * Compute all field statistics for flow field components
 */
static PyObject* compute_flow_statistics_py(PyObject* self, PyObject* args) {
    (void)self;
    PyObject* u_list;
    PyObject* v_list;
    PyObject* p_list;
    size_t nx, ny;

    if (!PyArg_ParseTuple(args, "OOOnn", &u_list, &v_list, &p_list, &nx, &ny)) {
        return NULL;
    }

    if (!PyList_Check(u_list) || !PyList_Check(v_list) || !PyList_Check(p_list)) {
        PyErr_SetString(PyExc_TypeError, "u, v, and p must be lists");
        return NULL;
    }

    size_t size = nx * ny;
    if ((size_t)PyList_Size(u_list) != size ||
        (size_t)PyList_Size(v_list) != size ||
        (size_t)PyList_Size(p_list) != size) {
        PyErr_Format(PyExc_ValueError,
                     "All fields must have size nx*ny (%zu)", size);
        return NULL;
    }

    // Create a temporary flow_field structure
    flow_field* field = flow_field_create(nx, ny);
    if (field == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate flow field");
        return NULL;
    }

    // Copy data from lists
    for (size_t i = 0; i < size; i++) {
        field->u[i] = PyFloat_AsDouble(PyList_GetItem(u_list, i));
        field->v[i] = PyFloat_AsDouble(PyList_GetItem(v_list, i));
        field->p[i] = PyFloat_AsDouble(PyList_GetItem(p_list, i));
        if (PyErr_Occurred()) {
            flow_field_destroy(field);
            return NULL;
        }
    }

    // Create derived fields and compute statistics
    derived_fields* derived = derived_fields_create(nx, ny);
    if (derived == NULL) {
        flow_field_destroy(field);
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate derived fields");
        return NULL;
    }

    // First compute velocity magnitude (required for vel_mag_stats)
    derived_fields_compute_velocity_magnitude(derived, field);
    // Then compute all statistics
    derived_fields_compute_statistics(derived, field);

    // Build result dictionary with all statistics
    PyObject* result = PyDict_New();
    if (result == NULL) {
        derived_fields_destroy(derived);
        flow_field_destroy(field);
        return NULL;
    }

    // Helper macro to add stats dict (properly handles reference counts and errors)
    #define ADD_STATS(name, stats_struct) do { \
        PyObject* stats_dict = PyDict_New(); \
        if (stats_dict == NULL) { \
            Py_DECREF(result); \
            derived_fields_destroy(derived); \
            flow_field_destroy(field); \
            return NULL; \
        } \
        PyObject* tmp_min = PyFloat_FromDouble((stats_struct).min_val); \
        PyObject* tmp_max = PyFloat_FromDouble((stats_struct).max_val); \
        PyObject* tmp_avg = PyFloat_FromDouble((stats_struct).avg_val); \
        PyObject* tmp_sum = PyFloat_FromDouble((stats_struct).sum_val); \
        if (tmp_min == NULL || tmp_max == NULL || tmp_avg == NULL || tmp_sum == NULL) { \
            Py_XDECREF(tmp_min); \
            Py_XDECREF(tmp_max); \
            Py_XDECREF(tmp_avg); \
            Py_XDECREF(tmp_sum); \
            Py_DECREF(stats_dict); \
            Py_DECREF(result); \
            derived_fields_destroy(derived); \
            flow_field_destroy(field); \
            return NULL; \
        } \
        if (PyDict_SetItemString(stats_dict, "min", tmp_min) < 0 || \
            PyDict_SetItemString(stats_dict, "max", tmp_max) < 0 || \
            PyDict_SetItemString(stats_dict, "avg", tmp_avg) < 0 || \
            PyDict_SetItemString(stats_dict, "sum", tmp_sum) < 0) { \
            Py_DECREF(tmp_min); \
            Py_DECREF(tmp_max); \
            Py_DECREF(tmp_avg); \
            Py_DECREF(tmp_sum); \
            Py_DECREF(stats_dict); \
            Py_DECREF(result); \
            derived_fields_destroy(derived); \
            flow_field_destroy(field); \
            return NULL; \
        } \
        Py_DECREF(tmp_min); \
        Py_DECREF(tmp_max); \
        Py_DECREF(tmp_avg); \
        Py_DECREF(tmp_sum); \
        if (PyDict_SetItemString(result, name, stats_dict) < 0) { \
            Py_DECREF(stats_dict); \
            Py_DECREF(result); \
            derived_fields_destroy(derived); \
            flow_field_destroy(field); \
            return NULL; \
        } \
        Py_DECREF(stats_dict); \
    } while(0)

    ADD_STATS("u", derived->u_stats);
    ADD_STATS("v", derived->v_stats);
    ADD_STATS("p", derived->p_stats);
    ADD_STATS("velocity_magnitude", derived->vel_mag_stats);

    #undef ADD_STATS

    derived_fields_destroy(derived);
    flow_field_destroy(field);

    return result;
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
     "    output_dir (str): Base directory path for outputs\n\n"
     "Note: Deprecated. Use simulation context instead."},
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
    {"get_last_error", get_last_error, METH_NOARGS,
     "Get the last CFD library error message.\n\n"
     "Returns:\n"
     "    str or None: Error message, or None if no error"},
    {"get_last_status", get_last_status, METH_NOARGS,
     "Get the last CFD library status code.\n\n"
     "Returns:\n"
     "    int: Status code (0 = success, negative = error)"},
    {"clear_error", clear_error, METH_NOARGS,
     "Clear the CFD library error state."},
    {"get_error_string", get_error_string, METH_VARARGS,
     "Get human-readable string for a status code.\n\n"
     "Args:\n"
     "    status (int): Status code\n\n"
     "Returns:\n"
     "    str: Description of the status code"},
    // Boundary Conditions API
    {"bc_get_backend", bc_get_backend_py, METH_NOARGS,
     "Get the current BC backend.\n\n"
     "Returns:\n"
     "    int: Backend type (BC_BACKEND_AUTO, BC_BACKEND_SCALAR, etc.)"},
    {"bc_get_backend_name", bc_get_backend_name_py, METH_NOARGS,
     "Get the name of the current BC backend.\n\n"
     "Returns:\n"
     "    str: Backend name (e.g., 'scalar', 'simd', 'omp')"},
    {"bc_set_backend", bc_set_backend_py, METH_VARARGS,
     "Set the BC backend.\n\n"
     "Args:\n"
     "    backend (int): Backend type constant\n\n"
     "Returns:\n"
     "    bool: True if backend was set successfully"},
    {"bc_backend_available", bc_backend_available_py, METH_VARARGS,
     "Check if a BC backend is available.\n\n"
     "Args:\n"
     "    backend (int): Backend type constant\n\n"
     "Returns:\n"
     "    bool: True if backend is available"},
    {"bc_apply_scalar", (PyCFunction)bc_apply_scalar_py, METH_VARARGS | METH_KEYWORDS,
     "Apply boundary conditions to a scalar field.\n\n"
     "Args:\n"
     "    field (list): Scalar field data (modified in-place)\n"
     "    nx (int): Grid points in x direction\n"
     "    ny (int): Grid points in y direction\n"
     "    bc_type (int): Boundary condition type constant"},
    {"bc_apply_velocity", (PyCFunction)bc_apply_velocity_py, METH_VARARGS | METH_KEYWORDS,
     "Apply boundary conditions to velocity fields.\n\n"
     "Args:\n"
     "    u (list): X-velocity field (modified in-place)\n"
     "    v (list): Y-velocity field (modified in-place)\n"
     "    nx (int): Grid points in x direction\n"
     "    ny (int): Grid points in y direction\n"
     "    bc_type (int): Boundary condition type constant"},
    {"bc_apply_dirichlet", (PyCFunction)bc_apply_dirichlet_scalar_py, METH_VARARGS | METH_KEYWORDS,
     "Apply Dirichlet (fixed value) boundary conditions.\n\n"
     "Args:\n"
     "    field (list): Scalar field data (modified in-place)\n"
     "    nx (int): Grid points in x direction\n"
     "    ny (int): Grid points in y direction\n"
     "    left (float): Value at left boundary\n"
     "    right (float): Value at right boundary\n"
     "    bottom (float): Value at bottom boundary\n"
     "    top (float): Value at top boundary"},
    {"bc_apply_noslip", (PyCFunction)bc_apply_noslip_py, METH_VARARGS | METH_KEYWORDS,
     "Apply no-slip wall boundary conditions (zero velocity).\n\n"
     "Args:\n"
     "    u (list): X-velocity field (modified in-place)\n"
     "    v (list): Y-velocity field (modified in-place)\n"
     "    nx (int): Grid points in x direction\n"
     "    ny (int): Grid points in y direction"},
    {"bc_apply_inlet_uniform", (PyCFunction)bc_apply_inlet_uniform_py, METH_VARARGS | METH_KEYWORDS,
     "Apply uniform inlet velocity boundary condition.\n\n"
     "Args:\n"
     "    u (list): X-velocity field (modified in-place)\n"
     "    v (list): Y-velocity field (modified in-place)\n"
     "    nx (int): Grid points in x direction\n"
     "    ny (int): Grid points in y direction\n"
     "    u_inlet (float): X-velocity at inlet\n"
     "    v_inlet (float): Y-velocity at inlet\n"
     "    edge (int, optional): Boundary edge (default: BC_EDGE_LEFT)"},
    {"bc_apply_inlet_parabolic", (PyCFunction)bc_apply_inlet_parabolic_py, METH_VARARGS | METH_KEYWORDS,
     "Apply parabolic inlet velocity profile.\n\n"
     "Args:\n"
     "    u (list): X-velocity field (modified in-place)\n"
     "    v (list): Y-velocity field (modified in-place)\n"
     "    nx (int): Grid points in x direction\n"
     "    ny (int): Grid points in y direction\n"
     "    max_velocity (float): Maximum velocity at profile center\n"
     "    edge (int, optional): Boundary edge (default: BC_EDGE_LEFT)"},
    {"bc_apply_outlet_scalar", (PyCFunction)bc_apply_outlet_scalar_py, METH_VARARGS | METH_KEYWORDS,
     "Apply outlet (zero-gradient) boundary condition to scalar field.\n\n"
     "Args:\n"
     "    field (list): Scalar field data (modified in-place)\n"
     "    nx (int): Grid points in x direction\n"
     "    ny (int): Grid points in y direction\n"
     "    edge (int, optional): Boundary edge (default: BC_EDGE_RIGHT)"},
    {"bc_apply_outlet_velocity", (PyCFunction)bc_apply_outlet_velocity_py, METH_VARARGS | METH_KEYWORDS,
     "Apply outlet (zero-gradient) boundary condition to velocity fields.\n\n"
     "Args:\n"
     "    u (list): X-velocity field (modified in-place)\n"
     "    v (list): Y-velocity field (modified in-place)\n"
     "    nx (int): Grid points in x direction\n"
     "    ny (int): Grid points in y direction\n"
     "    edge (int, optional): Boundary edge (default: BC_EDGE_RIGHT)"},
    // Derived Fields API (Phase 3)
    {"calculate_field_stats", calculate_field_stats_py, METH_VARARGS,
     "Calculate statistics (min, max, avg, sum) for a field.\n\n"
     "Args:\n"
     "    data (list): Field data as flat list\n\n"
     "Returns:\n"
     "    dict: Statistics with keys 'min', 'max', 'avg', 'sum'"},
    {"compute_velocity_magnitude", compute_velocity_magnitude_py, METH_VARARGS,
     "Compute velocity magnitude from u and v components.\n\n"
     "Args:\n"
     "    u (list): X-velocity field\n"
     "    v (list): Y-velocity field\n"
     "    nx (int): Grid points in x direction\n"
     "    ny (int): Grid points in y direction\n\n"
     "Returns:\n"
     "    list: Velocity magnitude field (sqrt(u^2 + v^2))"},
    {"compute_flow_statistics", compute_flow_statistics_py, METH_VARARGS,
     "Compute statistics for all flow field components.\n\n"
     "Args:\n"
     "    u (list): X-velocity field\n"
     "    v (list): Y-velocity field\n"
     "    p (list): Pressure field\n"
     "    nx (int): Grid points in x direction\n"
     "    ny (int): Grid points in y direction\n\n"
     "Returns:\n"
     "    dict: Statistics for 'u', 'v', 'p', 'velocity_magnitude'\n"
     "          Each contains 'min', 'max', 'avg', 'sum'"},
    // Solver Backend Availability API (v0.1.6)
    {"backend_is_available", backend_is_available_py, METH_VARARGS,
     "Check if a solver backend is available at runtime.\n\n"
     "Args:\n"
     "    backend (int): Backend type (BACKEND_SCALAR, BACKEND_SIMD, etc.)\n\n"
     "Returns:\n"
     "    bool: True if backend is available"},
    {"backend_get_name", backend_get_name_py, METH_VARARGS,
     "Get human-readable name for a solver backend.\n\n"
     "Args:\n"
     "    backend (int): Backend type constant\n\n"
     "Returns:\n"
     "    str or None: Backend name (e.g., 'scalar', 'simd', 'omp', 'cuda')"},
    {"list_solvers_by_backend", list_solvers_by_backend_py, METH_VARARGS,
     "Get list of solver types for a specific backend.\n\n"
     "Args:\n"
     "    backend (int): Backend type constant\n\n"
     "Returns:\n"
     "    list: Solver type names for the specified backend"},
    {"get_available_backends", get_available_backends_py, METH_NOARGS,
     "Get list of all available backends.\n\n"
     "Returns:\n"
     "    list: Names of available backends (e.g., ['scalar', 'simd', 'omp'])"},
    // CPU Features API (Phase 6)
    {"get_simd_arch", get_simd_arch_py, METH_NOARGS,
     "Get the detected SIMD architecture.\n\n"
     "Returns:\n"
     "    int: SIMD_NONE (0), SIMD_AVX2 (1), or SIMD_NEON (2)"},
    {"get_simd_name", get_simd_name_py, METH_NOARGS,
     "Get the name of the detected SIMD architecture.\n\n"
     "Returns:\n"
     "    str: 'avx2', 'neon', or 'none'"},
    {"has_avx2", has_avx2_py, METH_NOARGS,
     "Check if AVX2 (x86-64) is available.\n\n"
     "Returns:\n"
     "    bool: True if AVX2 is available and usable"},
    {"has_neon", has_neon_py, METH_NOARGS,
     "Check if ARM NEON is available.\n\n"
     "Returns:\n"
     "    bool: True if ARM NEON is available"},
    {"has_simd", has_simd_py, METH_NOARGS,
     "Check if any SIMD (AVX2 or NEON) is available.\n\n"
     "Returns:\n"
     "    bool: True if any SIMD instruction set is available"},
    // Grid Initialization Variants (Phase 6)
    {"create_grid_stretched", create_grid_stretched_py, METH_VARARGS,
     "Create a grid with stretched (non-uniform) spacing.\n\n"
     "Uses hyperbolic cosine stretching to cluster points near boundaries.\n"
     "Larger beta values create more stretching.\n\n"
     "Args:\n"
     "    nx (int): Grid points in x direction\n"
     "    ny (int): Grid points in y direction\n"
     "    xmin (float): Minimum x coordinate\n"
     "    xmax (float): Maximum x coordinate\n"
     "    ymin (float): Minimum y coordinate\n"
     "    ymax (float): Maximum y coordinate\n"
     "    beta (float): Stretching factor (> 0, typically 1.0-3.0)\n\n"
     "Returns:\n"
     "    dict: Grid info with 'nx', 'ny', 'x', 'y', 'xmin', 'xmax', 'ymin', 'ymax', 'beta'"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef cfd_python_module = {
    PyModuleDef_HEAD_INIT,
    "cfd_python",
    "Python bindings for CFD simulation library v0.1.5+ with pluggable solver support.\n\n"
    "Available functions:\n"
    "  - list_solvers(): Get available solver types\n"
    "  - has_solver(name): Check if a solver exists\n"
    "  - get_solver_info(name): Get solver details\n"
    "  - run_simulation(...): Run a simulation\n"
    "  - run_simulation_with_params(...): Run with detailed parameters\n"
    "  - create_grid(...): Create a computational grid\n"
    "  - get_default_solver_params(): Get default parameters\n"
    "  - set_output_dir(path): Set output directory (deprecated)\n"
    "  - write_vtk_scalar(...): Write scalar VTK output\n"
    "  - write_vtk_vector(...): Write vector VTK output\n"
    "  - write_csv_timeseries(...): Write CSV timeseries\n"
    "  - get_last_error(): Get last error message\n"
    "  - get_last_status(): Get last status code\n"
    "  - clear_error(): Clear error state\n"
    "  - get_error_string(code): Get error description\n\n"
    "Available solver types:\n"
    "  - 'explicit_euler': Basic finite difference solver\n"
    "  - 'explicit_euler_optimized': SIMD-optimized solver\n"
    "  - 'explicit_euler_omp': OpenMP parallel Euler solver\n"
    "  - 'projection': Pressure-velocity projection solver\n"
    "  - 'projection_optimized': Optimized projection solver\n"
    "  - 'projection_omp': OpenMP parallel projection solver\n"
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
    if (PyModule_AddStringConstant(m, "__version__", "0.2.0") < 0) {
        Py_DECREF(m);
        return NULL;
    }

    // Create and initialize the solver registry (context-bound API)
    g_registry = cfd_registry_create();
    if (g_registry == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to create solver registry");
        Py_DECREF(m);
        return NULL;
    }
    cfd_registry_register_defaults(g_registry);

    // Dynamically add solver type constants from the registry
    // This automatically picks up any new solvers added to the C library
    const char* solver_names[32];
    int solver_count = cfd_registry_list(g_registry, solver_names, 32);
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
            char warn_msg[128];
            snprintf(warn_msg, sizeof(warn_msg),
                     "Solver name '%s' exceeds maximum length (%zu > %zu), skipping constant export",
                     solver_names[i], name_len, max_name_len);
            PyErr_WarnEx(PyExc_RuntimeWarning, warn_msg, 1);
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

    // Add output field type constants (new API uses OUTPUT_VELOCITY_MAGNITUDE instead of OUTPUT_PRESSURE)
    if (PyModule_AddIntConstant(m, "OUTPUT_VELOCITY_MAGNITUDE", OUTPUT_VELOCITY_MAGNITUDE) < 0 ||
        PyModule_AddIntConstant(m, "OUTPUT_VELOCITY", OUTPUT_VELOCITY) < 0 ||
        PyModule_AddIntConstant(m, "OUTPUT_FULL_FIELD", OUTPUT_FULL_FIELD) < 0 ||
        PyModule_AddIntConstant(m, "OUTPUT_CSV_TIMESERIES", OUTPUT_CSV_TIMESERIES) < 0 ||
        PyModule_AddIntConstant(m, "OUTPUT_CSV_CENTERLINE", OUTPUT_CSV_CENTERLINE) < 0 ||
        PyModule_AddIntConstant(m, "OUTPUT_CSV_STATISTICS", OUTPUT_CSV_STATISTICS) < 0) {
        Py_DECREF(m);
        return NULL;
    }

    // Add status code constants
    if (PyModule_AddIntConstant(m, "CFD_SUCCESS", CFD_SUCCESS) < 0 ||
        PyModule_AddIntConstant(m, "CFD_ERROR", CFD_ERROR) < 0 ||
        PyModule_AddIntConstant(m, "CFD_ERROR_NOMEM", CFD_ERROR_NOMEM) < 0 ||
        PyModule_AddIntConstant(m, "CFD_ERROR_INVALID", CFD_ERROR_INVALID) < 0 ||
        PyModule_AddIntConstant(m, "CFD_ERROR_IO", CFD_ERROR_IO) < 0 ||
        PyModule_AddIntConstant(m, "CFD_ERROR_UNSUPPORTED", CFD_ERROR_UNSUPPORTED) < 0 ||
        PyModule_AddIntConstant(m, "CFD_ERROR_DIVERGED", CFD_ERROR_DIVERGED) < 0 ||
        PyModule_AddIntConstant(m, "CFD_ERROR_MAX_ITER", CFD_ERROR_MAX_ITER) < 0) {
        Py_DECREF(m);
        return NULL;
    }

    // Add boundary condition type constants
    if (PyModule_AddIntConstant(m, "BC_TYPE_PERIODIC", BC_TYPE_PERIODIC) < 0 ||
        PyModule_AddIntConstant(m, "BC_TYPE_NEUMANN", BC_TYPE_NEUMANN) < 0 ||
        PyModule_AddIntConstant(m, "BC_TYPE_DIRICHLET", BC_TYPE_DIRICHLET) < 0 ||
        PyModule_AddIntConstant(m, "BC_TYPE_NOSLIP", BC_TYPE_NOSLIP) < 0 ||
        PyModule_AddIntConstant(m, "BC_TYPE_INLET", BC_TYPE_INLET) < 0 ||
        PyModule_AddIntConstant(m, "BC_TYPE_OUTLET", BC_TYPE_OUTLET) < 0) {
        Py_DECREF(m);
        return NULL;
    }

    // Add boundary edge constants
    if (PyModule_AddIntConstant(m, "BC_EDGE_LEFT", BC_EDGE_LEFT) < 0 ||
        PyModule_AddIntConstant(m, "BC_EDGE_RIGHT", BC_EDGE_RIGHT) < 0 ||
        PyModule_AddIntConstant(m, "BC_EDGE_BOTTOM", BC_EDGE_BOTTOM) < 0 ||
        PyModule_AddIntConstant(m, "BC_EDGE_TOP", BC_EDGE_TOP) < 0) {
        Py_DECREF(m);
        return NULL;
    }

    // Add boundary condition backend constants
    if (PyModule_AddIntConstant(m, "BC_BACKEND_AUTO", BC_BACKEND_AUTO) < 0 ||
        PyModule_AddIntConstant(m, "BC_BACKEND_SCALAR", BC_BACKEND_SCALAR) < 0 ||
        PyModule_AddIntConstant(m, "BC_BACKEND_OMP", BC_BACKEND_OMP) < 0 ||
        PyModule_AddIntConstant(m, "BC_BACKEND_SIMD", BC_BACKEND_SIMD) < 0 ||
        PyModule_AddIntConstant(m, "BC_BACKEND_CUDA", BC_BACKEND_CUDA) < 0) {
        Py_DECREF(m);
        return NULL;
    }

    // Add solver backend constants (v0.1.6 API)
    if (PyModule_AddIntConstant(m, "BACKEND_SCALAR", NS_SOLVER_BACKEND_SCALAR) < 0 ||
        PyModule_AddIntConstant(m, "BACKEND_SIMD", NS_SOLVER_BACKEND_SIMD) < 0 ||
        PyModule_AddIntConstant(m, "BACKEND_OMP", NS_SOLVER_BACKEND_OMP) < 0 ||
        PyModule_AddIntConstant(m, "BACKEND_CUDA", NS_SOLVER_BACKEND_CUDA) < 0) {
        Py_DECREF(m);
        return NULL;
    }

    // Add SIMD architecture constants (Phase 6)
    if (PyModule_AddIntConstant(m, "SIMD_NONE", CFD_SIMD_NONE) < 0 ||
        PyModule_AddIntConstant(m, "SIMD_AVX2", CFD_SIMD_AVX2) < 0 ||
        PyModule_AddIntConstant(m, "SIMD_NEON", CFD_SIMD_NEON) < 0) {
        Py_DECREF(m);
        return NULL;
    }

    return m;
}
