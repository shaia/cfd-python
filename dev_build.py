#!/usr/bin/env python3
"""
Build script for CFD Python

Usage:
    python build.py              # Build and install in development mode
    python build.py build        # Build only (no install)
    python build.py install      # Build and install
    python build.py test         # Run tests
    python build.py clean        # Clean build artifacts
    python build.py all          # Clean, build, install, and test
"""
import subprocess
import sys
import shutil
import argparse
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.resolve()
CFD_ROOT = PROJECT_ROOT.parent / "cfd"
BUILD_DIR = PROJECT_ROOT / "build"


def run(cmd, cwd=None, check=True):
    """Run a command and print it"""
    print(f">>> {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd or PROJECT_ROOT)
    if check and result.returncode != 0:
        sys.exit(result.returncode)
    return result


def build_cfd_library():
    """Build the C library (required before building Python extension)"""
    print("\n=== Building CFD C Library ===")

    if not CFD_ROOT.exists():
        print(f"ERROR: CFD library not found at {CFD_ROOT}")
        sys.exit(1)

    # Check for build script in cfd directory
    build_script = CFD_ROOT / "build.sh"
    if build_script.exists():
        run("./build.sh build", cwd=CFD_ROOT)
    else:
        # Use cmake directly
        run("cmake -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF", cwd=CFD_ROOT)
        run("cmake --build build --config Release", cwd=CFD_ROOT)


def build():
    """Build the Python extension"""
    print("\n=== Building Python Extension ===")

    # Ensure C library is built
    cfd_lib_dir = CFD_ROOT / "build" / "lib" / "Release"
    if not cfd_lib_dir.exists():
        build_cfd_library()

    # Build using pip
    run(f"{sys.executable} -m pip install --no-build-isolation -e .")


def install():
    """Install the package"""
    print("\n=== Installing Package ===")
    run(f"{sys.executable} -m pip install .")


def develop():
    """Install in development/editable mode"""
    print("\n=== Installing in Development Mode ===")
    run(f"{sys.executable} -m pip install -e .")


def test():
    """Run tests"""
    print("\n=== Running Tests ===")
    run(f"{sys.executable} -m pytest tests/ -v")


def clean():
    """Clean build artifacts"""
    print("\n=== Cleaning Build Artifacts ===")

    dirs_to_clean = [
        BUILD_DIR,
        PROJECT_ROOT / "dist",
        PROJECT_ROOT / "wheelhouse",
        PROJECT_ROOT / "cfd_python.egg-info",
        PROJECT_ROOT / ".pytest_cache",
    ]

    for d in dirs_to_clean:
        if d.exists():
            print(f"Removing {d}")
            shutil.rmtree(d)

    # Remove __pycache__ directories
    for pycache in PROJECT_ROOT.rglob("__pycache__"):
        print(f"Removing {pycache}")
        shutil.rmtree(pycache)

    # Remove .pyd/.so files (skip virtual environments)
    # Common venv directory names to exclude
    venv_patterns = {".venv", "venv", ".env", "env", "virtualenv", ".virtualenv"}
    for ext in ["*.pyd", "*.so"]:
        for f in PROJECT_ROOT.rglob(ext):
            # Check if any path component matches a venv pattern
            if not any(part in venv_patterns for part in f.parts):
                print(f"Removing {f}")
                f.unlink()


def verify():
    """Verify the installation works"""
    print("\n=== Verifying Installation ===")
    result = run(f'{sys.executable} -c "import cfd_python; print(f\'Version: {{cfd_python.__version__}}\'); print(f\'Solvers: {{cfd_python.list_solvers()}}\')"', check=False)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Build script for CFD Python")
    parser.add_argument(
        "command",
        nargs="?",
        default="develop",
        choices=["build", "install", "develop", "test", "clean", "all", "verify", "cfd"],
        help="Command to run (default: develop)"
    )

    args = parser.parse_args()

    if args.command == "build":
        build()
    elif args.command == "install":
        build_cfd_library()
        install()
    elif args.command == "develop":
        build_cfd_library()
        develop()
    elif args.command == "test":
        test()
    elif args.command == "clean":
        clean()
    elif args.command == "verify":
        verify()
    elif args.command == "cfd":
        build_cfd_library()
    elif args.command == "all":
        clean()
        build_cfd_library()
        develop()
        if verify():
            test()
        else:
            print("ERROR: Verification failed")
            sys.exit(1)

    print("\nDone!")


if __name__ == "__main__":
    main()
