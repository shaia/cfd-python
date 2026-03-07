#!/usr/bin/env python3
"""
Logging Example (v0.2.0)

Demonstrates the Python logging callback API introduced in v0.2.0.
The C library emits log messages during simulation (convergence info,
warnings, errors). set_log_callback() lets you capture these in Python
for monitoring, debugging, or integration with Python's logging module.

Log levels:
- CFD_LOG_LEVEL_INFO:    Informational (convergence, progress)
- CFD_LOG_LEVEL_WARNING: Warnings (slow convergence, near-limits)
- CFD_LOG_LEVEL_ERROR:   Errors (divergence, failures)
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import cfd_python
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure to build the package first:")
    print("  pip install -e .")
    sys.exit(1)


# =================================================================
# Custom callback approaches
# =================================================================


def simple_callback(level, message):
    """Simple callback that prints messages with a level prefix."""
    prefixes = {
        cfd_python.CFD_LOG_LEVEL_INFO: "INFO",
        cfd_python.CFD_LOG_LEVEL_WARNING: "WARN",
        cfd_python.CFD_LOG_LEVEL_ERROR: "ERROR",
    }
    prefix = prefixes.get(level, f"LEVEL_{level}")
    print(f"   [{prefix}] {message}")


class LogCollector:
    """Collects log messages for later analysis."""

    def __init__(self):
        self.messages = []

    def __call__(self, level, message):
        self.messages.append({"level": level, "message": message})

    def summary(self):
        info = sum(1 for m in self.messages if m["level"] == cfd_python.CFD_LOG_LEVEL_INFO)
        warn = sum(1 for m in self.messages if m["level"] == cfd_python.CFD_LOG_LEVEL_WARNING)
        err = sum(1 for m in self.messages if m["level"] == cfd_python.CFD_LOG_LEVEL_ERROR)
        return {"total": len(self.messages), "info": info, "warnings": warn, "errors": err}


def make_python_logging_callback(logger_name="cfd_python"):
    """Bridge CFD log messages to Python's standard logging module."""
    logger = logging.getLogger(logger_name)

    level_map = {
        cfd_python.CFD_LOG_LEVEL_INFO: logging.INFO,
        cfd_python.CFD_LOG_LEVEL_WARNING: logging.WARNING,
        cfd_python.CFD_LOG_LEVEL_ERROR: logging.ERROR,
    }

    def callback(level, message):
        py_level = level_map.get(level, logging.DEBUG)
        logger.log(py_level, message)

    return callback


def main():
    print("CFD Python Logging Example (v0.2.0)")
    print("=" * 60)

    # =================================================================
    # 1. Log Level Constants
    # =================================================================
    print("\n1. Log Level Constants")
    print("-" * 60)
    print(f"   CFD_LOG_LEVEL_INFO    = {cfd_python.CFD_LOG_LEVEL_INFO}")
    print(f"   CFD_LOG_LEVEL_WARNING = {cfd_python.CFD_LOG_LEVEL_WARNING}")
    print(f"   CFD_LOG_LEVEL_ERROR   = {cfd_python.CFD_LOG_LEVEL_ERROR}")

    # =================================================================
    # 2. Simple Callback
    # =================================================================
    print("\n2. Simple Callback")
    print("-" * 60)
    print("   Setting simple_callback as log handler...")

    cfd_python.set_log_callback(simple_callback)

    # Run a small simulation to generate log messages
    cfd_python.run_simulation(nx=10, ny=10, steps=5)

    # =================================================================
    # 3. Collector Callback
    # =================================================================
    print("\n3. Log Collector")
    print("-" * 60)

    collector = LogCollector()
    cfd_python.set_log_callback(collector)

    # Run simulation — messages are collected silently
    cfd_python.run_simulation(nx=10, ny=10, steps=10)

    summary = collector.summary()
    print(f"   Collected {summary['total']} messages:")
    print(f"     Info:     {summary['info']}")
    print(f"     Warnings: {summary['warnings']}")
    print(f"     Errors:   {summary['errors']}")

    # Show collected messages
    if collector.messages:
        print("\n   Last few messages:")
        for msg in collector.messages[-3:]:
            level_name = {
                cfd_python.CFD_LOG_LEVEL_INFO: "INFO",
                cfd_python.CFD_LOG_LEVEL_WARNING: "WARN",
                cfd_python.CFD_LOG_LEVEL_ERROR: "ERROR",
            }.get(msg["level"], "?")
            print(f"     [{level_name}] {msg['message']}")

    # =================================================================
    # 4. Python logging Integration
    # =================================================================
    print("\n4. Python logging Module Integration")
    print("-" * 60)

    # Configure Python's logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="   %(name)s [%(levelname)s] %(message)s",
    )

    callback = make_python_logging_callback("cfd_python.engine")
    cfd_python.set_log_callback(callback)

    print("   Running simulation with Python logging bridge...")
    cfd_python.run_simulation(nx=10, ny=10, steps=5)

    # =================================================================
    # 5. Clearing the Callback
    # =================================================================
    print("\n5. Clearing the Callback")
    print("-" * 60)

    # Pass None to disable logging
    cfd_python.set_log_callback(None)
    print("   Log callback cleared (messages discarded)")

    # This simulation runs silently
    cfd_python.run_simulation(nx=10, ny=10, steps=5)
    print("   Simulation completed silently")

    # =================================================================
    # Summary
    # =================================================================
    print("\n" + "=" * 60)
    print("Summary")
    print("-" * 60)
    print("   Callback patterns:")
    print("     1. Simple function: quick debugging")
    print("     2. Class with __call__: collect and analyze")
    print("     3. logging bridge: production integration")
    print("     4. None: disable logging")


if __name__ == "__main__":
    main()
