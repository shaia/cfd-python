cmake_minimum_required(VERSION 3.15...3.27)

project(cfd_python LANGUAGES C)

# Option to control static vs dynamic linking
if(DEFINED ENV{CFD_STATIC_LINK})
    set(CFD_STATIC_LINK_DEFAULT $ENV{CFD_STATIC_LINK})
else()
    set(CFD_STATIC_LINK_DEFAULT ON)
endif()
option(CFD_STATIC_LINK "Statically link the CFD library" ${CFD_STATIC_LINK_DEFAULT})

# Option to use stable ABI (abi3)
option(CFD_USE_STABLE_ABI "Build with Python stable ABI for cross-version compatibility" ON)

# Debug output
message(STATUS "CFD_STATIC_LINK: ${CFD_STATIC_LINK}")
message(STATUS "CFD_USE_STABLE_ABI: ${CFD_USE_STABLE_ABI}")
message(STATUS "CFD_ROOT env: $ENV{CFD_ROOT}")

# Find Python
find_package(Python 3.8 REQUIRED COMPONENTS Interpreter Development.Module)
message(STATUS "Python version: ${Python_VERSION}")
message(STATUS "Python executable: ${Python_EXECUTABLE}")

# Find CFD library
if(DEFINED ENV{CFD_ROOT})
    set(CFD_ROOT_DIR "$ENV{CFD_ROOT}")
else()
    set(CFD_ROOT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../cfd")
endif()
message(STATUS "CFD_ROOT_DIR: ${CFD_ROOT_DIR}")

# Source headers in lib/include, generated headers (cfd_export.h) in build/lib/include
set(CFD_INCLUDE_DIR "${CFD_ROOT_DIR}/lib/include")
set(CFD_BUILD_INCLUDE_DIR "${CFD_ROOT_DIR}/build/lib/include")
set(CFD_LIBRARY_DIRS
    "${CFD_ROOT_DIR}/build/lib/Release"
    "${CFD_ROOT_DIR}/build/lib"
)

find_library(CFD_LIBRARY
    NAMES cfd_library cfd_library_static
    PATHS ${CFD_LIBRARY_DIRS}
    NO_DEFAULT_PATH
)

if(NOT CFD_LIBRARY)
    message(FATAL_ERROR "CFD library not found in ${CFD_LIBRARY_DIRS}")
endif()

message(STATUS "Found CFD library: ${CFD_LIBRARY}")
message(STATUS "CFD include dir: ${CFD_INCLUDE_DIR}")

# Create the Python extension module
# For stable ABI on Windows, we need to manually create the library
# to avoid Python_add_library linking against version-specific python3X.lib
if(CFD_USE_STABLE_ABI AND WIN32)
    # Create module manually for Windows stable ABI
    add_library(cfd_python MODULE src/cfd_python.c)

    set_target_properties(cfd_python PROPERTIES
        C_STANDARD 11
        PREFIX ""
        SUFFIX ".pyd"
    )

    # Define Py_LIMITED_API for stable ABI
    target_compile_definitions(cfd_python PRIVATE Py_LIMITED_API=0x03080000)

    # Find and link python3.lib (stable ABI library)
    get_filename_component(PYTHON_DIR "${Python_EXECUTABLE}" DIRECTORY)
    # Try multiple possible locations for python3.lib
    find_library(PYTHON3_STABLE_LIB
        NAMES python3
        PATHS
            "${PYTHON_DIR}/libs"
            "${PYTHON_DIR}/../libs"
            "${Python_LIBRARY_DIRS}"
        NO_DEFAULT_PATH
    )
    if(NOT PYTHON3_STABLE_LIB)
        # Last resort: construct path directly
        if(EXISTS "${PYTHON_DIR}/libs/python3.lib")
            set(PYTHON3_STABLE_LIB "${PYTHON_DIR}/libs/python3.lib")
        elseif(EXISTS "${PYTHON_DIR}/../libs/python3.lib")
            set(PYTHON3_STABLE_LIB "${PYTHON_DIR}/../libs/python3.lib")
        endif()
    endif()

    if(PYTHON3_STABLE_LIB)
        target_link_libraries(cfd_python PRIVATE ${PYTHON3_STABLE_LIB})
        message(STATUS "Linking against stable ABI library: ${PYTHON3_STABLE_LIB}")
    else()
        message(FATAL_ERROR "Could not find python3.lib for stable ABI linking")
    endif()

    message(STATUS "Building Windows stable ABI extension")
else()
    # Use Python_add_library for Unix or non-stable-ABI builds
    Python_add_library(cfd_python MODULE WITH_SOABI
        src/cfd_python.c
    )

    set_target_properties(cfd_python PROPERTIES
        C_STANDARD 11
    )

    if(CFD_USE_STABLE_ABI)
        target_compile_definitions(cfd_python PRIVATE Py_LIMITED_API=0x03080000)
        set_target_properties(cfd_python PROPERTIES SUFFIX ".abi3.so")
        message(STATUS "Building Unix stable ABI extension")
    endif()
endif()

target_include_directories(cfd_python PRIVATE
    ${CFD_INCLUDE_DIR}
    ${CFD_BUILD_INCLUDE_DIR}
    ${Python_INCLUDE_DIRS}
)

target_link_libraries(cfd_python PRIVATE
    ${CFD_LIBRARY}
)

# Install the extension module
install(TARGETS cfd_python DESTINATION cfd_python)
