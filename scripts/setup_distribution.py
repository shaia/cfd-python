#!/usr/bin/env python3
"""
Setup script for CFD Python distribution

This script helps set up the optimal distribution strategy for CFD Python.
"""

import os
import sys
import subprocess
import shlex
import shutil
from pathlib import Path

def run_command(cmd, cwd=None, check=True, env=None):
    """Run a command and return the result.

    Args:
        cmd: Command as a list of arguments (preferred) or a string.
             If a string is passed, it will be parsed using shlex.split.
        cwd: Working directory for the command.
        check: If True, raise CalledProcessError on non-zero exit.
        env: Environment variables for the subprocess.
    """
    # Convert string commands to argument lists for security (no shell=True)
    if isinstance(cmd, str):
        args = shlex.split(cmd)
    else:
        args = cmd

    print(f"Running: {' '.join(args)}")
    try:
        result = subprocess.run(args, cwd=cwd, check=check,
                              capture_output=True, text=True, env=env)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        raise

def embed_c_library():
    """Embed the C library source code into the Python package"""
    print("Embedding C library source code...")

    # Paths
    cfd_root = Path("../cfd").resolve()
    python_root = Path(".").resolve()
    target_dir = python_root / "src" / "cfd_lib"

    if not cfd_root.exists():
        print(f"ERROR: CFD library not found at: {cfd_root}")
        print("Please ensure the CFD library is in the parent directory")
        return False

    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)

    # Copy header files
    include_src = cfd_root / "lib" / "include"
    include_dst = target_dir / "include"
    if include_dst.exists():
        shutil.rmtree(include_dst)
    shutil.copytree(include_src, include_dst)
    print(f"OK: Copied headers: {include_src} -> {include_dst}")

    # Copy source files
    src_src = cfd_root / "lib" / "src"
    src_dst = target_dir / "src"
    if src_dst.exists():
        shutil.rmtree(src_dst)
    shutil.copytree(src_src, src_dst)
    print(f"OK: Copied sources: {src_src} -> {src_dst}")

    # Create embedded CMakeLists.txt
    cmake_content = '''
# Embedded CFD Library
cmake_minimum_required(VERSION 3.15)

# Create CFD library
add_library(cfd_library STATIC
    src/grid.c
    src/solver.c
    src/solver_optimized.c
    src/utils.c
    src/vtk_output.c
    src/simulation_api.c
)

target_include_directories(cfd_library PUBLIC include)

# Set library properties
set_target_properties(cfd_library PROPERTIES
    C_STANDARD 11
    POSITION_INDEPENDENT_CODE ON
)
'''

    cmake_file = target_dir / "CMakeLists.txt"
    cmake_file.write_text(cmake_content.strip())
    print("OK: Created embedded CMakeLists.txt")

    return True

def update_main_cmake():
    """Update the main CMakeLists.txt to use embedded library"""
    print("Updating main CMakeLists.txt...")

    cmake_content = '''cmake_minimum_required(VERSION 3.15...3.27)

project(cfd_python LANGUAGES C CXX)

# Find Python and required components
find_package(Python 3.8 REQUIRED COMPONENTS Interpreter Development.Module)

# Enable stable ABI (abi3) for Python 3.8+
if(${Python_VERSION} VERSION_GREATER_EQUAL "3.8")
    set(CMAKE_C_VISIBILITY_PRESET hidden)
    set(CMAKE_CXX_VISIBILITY_PRESET hidden)
    add_definitions(-DPy_LIMITED_API=0x03080000)
endif()

# Build embedded CFD library
add_subdirectory(src/cfd_lib)

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
    src/cfd_lib/include
    ${Python_INCLUDE_DIRS}
)

# Link libraries
target_link_libraries(cfd_python PRIVATE
    cfd_library
)

# On Windows, Python extension modules using stable ABI should not link against
# version-specific Python libraries. The symbols are provided by the interpreter at runtime.
if(WIN32)
    # Exclude version-specific Python libs (python38.lib, python39.lib, etc.)
    foreach(PY_VER RANGE 8 15)
        target_link_options(cfd_python PRIVATE "/NODEFAULTLIB:python3${PY_VER}.lib")
    endforeach()
    target_link_options(cfd_python PRIVATE "/NODEFAULTLIB:python3.lib")
endif()

# Install the extension module in the cfd_python package directory
install(TARGETS cfd_python DESTINATION cfd_python)
'''

    cmake_file = Path("CMakeLists.txt")
    cmake_file.write_text(cmake_content.strip())
    print("OK: Updated main CMakeLists.txt")

    return True

def build_wheels_locally():
    """Build wheels locally for testing"""
    print("Building wheels locally...")

    # Install cibuildwheel if not present
    try:
        import cibuildwheel
    except ImportError:
        print("Installing cibuildwheel...")
        run_command(["pip", "install", "cibuildwheel"])

    # Build wheels
    env = os.environ.copy()
    # Build only for current Python version for testing
    env['CIBW_BUILD'] = f'cp{sys.version_info.major}{sys.version_info.minor}-*'

    result = run_command(
        ["python", "-m", "cibuildwheel", "--output-dir", "wheelhouse"],
        check=False,
        env=env
    )

    if result.returncode == 0:
        print("OK: Wheels built successfully in wheelhouse/")

        # List built wheels
        wheelhouse = Path("wheelhouse")
        if wheelhouse.exists():
            wheels = list(wheelhouse.glob("*.whl"))
            print(f"Built wheels: {[w.name for w in wheels]}")

        return True
    else:
        print("ERROR: Wheel building failed")
        return False

def test_wheel_installation():
    """Test wheel installation in a clean environment"""
    print("Testing wheel installation...")

    wheelhouse = Path("wheelhouse")
    wheels = list(wheelhouse.glob("*.whl"))

    if not wheels:
        print("ERROR: No wheels found to test")
        return False

    wheel_path = wheels[0]  # Test the first wheel

    # Create test environment
    test_env = Path("test_env")
    if test_env.exists():
        shutil.rmtree(test_env)

    # Create virtual environment
    run_command(["python", "-m", "venv", str(test_env)])

    # Install wheel in test environment
    if sys.platform == "win32":
        python_exe = test_env / "Scripts" / "python.exe"
    else:
        python_exe = test_env / "bin" / "python"

    run_command([str(python_exe), "-m", "pip", "install", str(wheel_path)])

    # Test the installation by writing script to a temp file
    # (avoids shell quoting issues with multi-line strings)
    test_script = '''\
import cfd_python
print(f"CFD Python version: {cfd_python.__version__}")

# Test basic functionality
vel_mag = cfd_python.run_simulation(5, 5, 3)
assert len(vel_mag) == 25, f"Expected 25 values, got {len(vel_mag)}"
print("OK: Basic simulation test passed")

grid_info = cfd_python.create_grid(5, 5, 0, 1, 0, 1)
assert grid_info["nx"] == 5, "Grid creation failed"
print("OK: Grid creation test passed")

params = cfd_python.get_default_solver_params()
assert "dt" in params, "Solver params missing"
print("OK: Solver params test passed")

print("All tests passed!")
'''

    # Write test script to a temporary file and execute it
    test_script_path = test_env / "test_install.py"
    test_script_path.write_text(test_script)

    result = subprocess.run(
        [str(python_exe), str(test_script_path)],
        capture_output=True,
        text=True
    )
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0 and result.stderr:
        print(f"stderr: {result.stderr}")

    # Cleanup
    shutil.rmtree(test_env)

    if result.returncode == 0:
        print("OK: Wheel installation and testing successful!")
        return True
    else:
        print("ERROR: Wheel testing failed")
        return False

def setup_pypi_config():
    """Set up PyPI configuration files"""
    print("Setting up PyPI configuration...")

    # Create .pypirc template
    pypirc_content = '''[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = REPLACE_WITH_YOUR_PYPI_TOKEN

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = REPLACE_WITH_YOUR_TEST_PYPI_TOKEN
'''

    print("PyPI configuration template:")
    print("1. Create ~/.pypirc with your PyPI tokens")
    print("2. Or use GitHub Actions secrets for automated publishing")
    print("3. Template saved to .pypirc.template")

    Path(".pypirc.template").write_text(pypirc_content.strip())

    return True

def main():
    """Main setup function"""
    print("CFD Python Distribution Setup")
    print("=" * 50)

    steps = [
        ("Embedding C library", embed_c_library),
        ("Updating CMake configuration", update_main_cmake),
        ("Building wheels locally", build_wheels_locally),
        ("Testing wheel installation", test_wheel_installation),
        ("Setting up PyPI configuration", setup_pypi_config),
    ]

    for step_name, step_func in steps:
        print(f"\n[STEP] {step_name}...")
        try:
            success = step_func()
            if success:
                print(f"OK: {step_name} completed successfully")
            else:
                print(f"ERROR: {step_name} failed")
                break
        except Exception as e:
            print(f"ERROR: {step_name} failed with error: {e}")
            break
    else:
        print("\nDistribution setup completed successfully!")
        print("\nNext steps:")
        print("1. Push to GitHub to trigger automated wheel building")
        print("2. Create a release to publish to PyPI")
        print("3. Users can install with: pip install cfd-python")
        return True

    print("\nERROR: Distribution setup incomplete")
    return False

if __name__ == "__main__":
    main()