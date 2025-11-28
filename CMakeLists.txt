cmake_minimum_required(VERSION 3.15...3.27)

project(cfd_python LANGUAGES C CXX)

# Option to control static vs dynamic linking
option(CFD_STATIC_LINK "Statically link the CFD library" ON)

# Option to disable stable ABI (useful for development with Windows Store Python)
option(CFD_USE_STABLE_ABI "Use Python stable ABI (abi3)" OFF)

# Find Python and required components
find_package(Python 3.8 REQUIRED COMPONENTS Interpreter Development.Module)

# Enable stable ABI (abi3) for Python 3.8+ if requested
if(CFD_USE_STABLE_ABI AND ${Python_VERSION} VERSION_GREATER_EQUAL "3.8")
    set(CMAKE_C_VISIBILITY_PRESET hidden)
    set(CMAKE_CXX_VISIBILITY_PRESET hidden)
    add_definitions(-DPy_LIMITED_API=0x03080000)
    message(STATUS "Using Python stable ABI (abi3)")
endif()

# Find the CFD library from the parent project
# Check for CFD_ROOT environment variable, fall back to default location
if(DEFINED ENV{CFD_ROOT})
    set(CFD_ROOT_DIR "$ENV{CFD_ROOT}")
    message(STATUS "Using CFD_ROOT from environment: ${CFD_ROOT_DIR}")
else()
    set(CFD_ROOT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../cfd")
    message(STATUS "Using default CFD_ROOT: ${CFD_ROOT_DIR}")
endif()
set(CFD_INCLUDE_DIR "${CFD_ROOT_DIR}/lib/include")

# Determine library directory based on build type
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    set(CFD_LIBRARY_DIR "${CFD_ROOT_DIR}/build/lib/Debug")
else()
    set(CFD_LIBRARY_DIR "${CFD_ROOT_DIR}/build/lib/Release")
endif()

# Check if CFD library exists (prefer static library for packaging)
if(CFD_STATIC_LINK)
    # Look for static library first
    if(WIN32)
        find_library(CFD_LIBRARY
            NAMES cfd_library_static cfd_library
            PATHS ${CFD_LIBRARY_DIR}
            NO_DEFAULT_PATH
        )
    else()
        find_library(CFD_LIBRARY
            NAMES libcfd_library.a cfd_library
            PATHS ${CFD_LIBRARY_DIR}
            NO_DEFAULT_PATH
        )
    endif()
else()
    # Look for shared library
    find_library(CFD_LIBRARY
        NAMES cfd_library
        PATHS ${CFD_LIBRARY_DIR}
        NO_DEFAULT_PATH
    )
endif()

if(NOT CFD_LIBRARY)
    message(FATAL_ERROR "CFD library not found in ${CFD_LIBRARY_DIR}. Please build the C library first.")
endif()

message(STATUS "Found CFD library: ${CFD_LIBRARY}")
message(STATUS "CFD include directory: ${CFD_INCLUDE_DIR}")
message(STATUS "Static linking: ${CFD_STATIC_LINK}")

# Create the Python extension module
# Use WITH_SOABI to get proper ABI suffix for stable ABI builds
Python_add_library(cfd_python MODULE WITH_SOABI
    src/cfd_python.c
)

# Set properties for stable ABI
set_target_properties(cfd_python PROPERTIES
    C_STANDARD 11
    CXX_STANDARD 17
    INTERPROCEDURAL_OPTIMIZATION ON
)

# Use stable ABI if requested and available
if(CFD_USE_STABLE_ABI AND ${Python_VERSION} VERSION_GREATER_EQUAL "3.8")
    target_compile_definitions(cfd_python PRIVATE Py_LIMITED_API=0x03080000)
endif()

# Set proper extension name
if(WIN32)
    set_target_properties(cfd_python PROPERTIES SUFFIX ".pyd")
endif()

# Include directories
target_include_directories(cfd_python PRIVATE
    ${CFD_INCLUDE_DIR}
    ${Python_INCLUDE_DIRS}
)

# Link libraries
target_link_libraries(cfd_python PRIVATE
    ${CFD_LIBRARY}
)

# On Windows, handle stable ABI linking explicitly
if(WIN32)
    if(CFD_USE_STABLE_ABI)
        # For stable ABI, we need to link against python3.lib
        # Find the Python library directory and link python3.lib explicitly
        get_filename_component(Python_LIBRARY_DIR "${Python_LIBRARY_DIRS}" ABSOLUTE)
        if(NOT Python_LIBRARY_DIR)
            # Fallback: derive from Python executable path
            get_filename_component(Python_ROOT "${Python_EXECUTABLE}" DIRECTORY)
            set(Python_LIBRARY_DIR "${Python_ROOT}/libs")
        endif()
        find_library(Python3_LIBRARY
            NAMES python3
            PATHS "${Python_LIBRARY_DIR}"
            NO_DEFAULT_PATH
        )
        if(Python3_LIBRARY)
            message(STATUS "Using stable ABI library: ${Python3_LIBRARY}")
            target_link_libraries(cfd_python PRIVATE ${Python3_LIBRARY})
        else()
            message(WARNING "python3.lib not found, falling back to versioned library")
            target_link_libraries(cfd_python PRIVATE Python::Module)
        endif()
    else()
        # For non-stable ABI, use the versioned library
        target_link_libraries(cfd_python PRIVATE Python::Module)
    endif()
endif()

# Install the extension module in the cfd_python package directory
install(TARGETS cfd_python DESTINATION cfd_python)