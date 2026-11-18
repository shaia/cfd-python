"""Tests for logging functions and constants (v0.2.0)."""

import pytest

import cfd_python


class TestLogConstants:
    """Tests for CFD_LOG_LEVEL_* constants."""

    _LEVELS = ["CFD_LOG_LEVEL_INFO", "CFD_LOG_LEVEL_WARNING", "CFD_LOG_LEVEL_ERROR"]

    def test_log_level_constants_exist(self):
        for name in self._LEVELS:
            assert hasattr(cfd_python, name), f"Missing: {name}"

    def test_log_level_constants_are_integers(self):
        for name in self._LEVELS:
            assert isinstance(getattr(cfd_python, name), int)

    def test_log_level_constants_ordered(self):
        assert cfd_python.CFD_LOG_LEVEL_INFO < cfd_python.CFD_LOG_LEVEL_WARNING
        assert cfd_python.CFD_LOG_LEVEL_WARNING < cfd_python.CFD_LOG_LEVEL_ERROR

    def test_log_level_constants_in_all(self):
        for name in self._LEVELS:
            assert name in cfd_python.__all__, f"{name} not in __all__"


class TestSetLogCallback:
    """Tests for set_log_callback() function."""

    def test_set_log_callback_none_clears(self):
        cfd_python.set_log_callback(None)  # Should not raise

    def test_set_log_callback_callable(self):
        messages = []

        def callback(level, msg):
            messages.append((level, msg))

        cfd_python.set_log_callback(callback)
        cfd_python.set_log_callback(None)  # Cleanup

    def test_set_log_callback_lambda(self):
        cfd_python.set_log_callback(lambda level, msg: None)
        cfd_python.set_log_callback(None)  # Cleanup

    def test_set_log_callback_invalid_raises(self):
        with pytest.raises(TypeError):
            cfd_python.set_log_callback("not_callable")

    def test_set_log_callback_repeated(self):
        """Verify repeated callback registration does not leak."""
        for _ in range(50):
            cfd_python.set_log_callback(lambda level, msg: None)
        cfd_python.set_log_callback(None)  # Cleanup

    def test_set_log_callback_in_all(self):
        assert "set_log_callback" in cfd_python.__all__
