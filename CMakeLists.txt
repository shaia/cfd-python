cmake_minimum_required(VERSION 3.15...3.27)

project(cfd_python LANGUAGES C CXX)

# Option to control static vs dynamic linking
option(CFD_STATIC_LINK "Statically link the CFD library" ON)

# Find Python and required components
find_package(Python 3.8 REQUIRED COMPONENTS Interpreter Development.Module)

# Enable stable ABI (abi3) for Python 3.8+
if(${Python_VERSION} VERSION_GREATER_EQUAL "3.8")
    set(CMAKE_C_VISIBILITY_PRESET hidden)
    set(CMAKE_CXX_VISIBILITY_PRESET hidden)
    add_definitions(-DPy_LIMITED_API=0x03080000)
endif()

# Find the CFD library from the parent project
set(CFD_ROOT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../cfd")
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
Python_add_library(cfd_python MODULE
    src/cfd_python.c
)

# Set properties for stable ABI
set_target_properties(cfd_python PROPERTIES
    C_STANDARD 11
    CXX_STANDARD 17
    INTERPROCEDURAL_OPTIMIZATION ON
)

# Use stable ABI if available
if(${Python_VERSION} VERSION_GREATER_EQUAL "3.8")
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

# On Windows, Python extension modules should not link against Python libraries
# The symbols are provided by the Python interpreter at runtime
if(WIN32)
    target_link_options(cfd_python PRIVATE "/NODEFAULTLIB:python311.lib")
    target_link_options(cfd_python PRIVATE "/NODEFAULTLIB:python3.lib")
endif()

# Install the extension module in the cfd_python package directory
install(TARGETS cfd_python DESTINATION cfd_python)