"""Tests for GPU device management functions (v0.2.0)."""

import pytest

import cfd_python


class TestGPUFunctions:
    """Tests for gpu_is_available(), gpu_get_device_info(), etc."""

    def test_gpu_is_available_returns_bool(self):
        result = cfd_python.gpu_is_available()
        assert isinstance(result, bool)

    def test_gpu_get_device_info_returns_list(self):
        result = cfd_python.gpu_get_device_info()
        assert isinstance(result, list)

    def test_gpu_get_device_info_entries_are_dicts(self):
        devices = cfd_python.gpu_get_device_info()
        for device in devices:
            assert isinstance(device, dict)

    def test_gpu_get_default_config_returns_dict(self):
        result = cfd_python.gpu_get_default_config()
        assert isinstance(result, dict)

    def test_gpu_is_available_consistent_with_device_info(self):
        available = cfd_python.gpu_is_available()
        devices = cfd_python.gpu_get_device_info()
        if available:
            assert len(devices) > 0
        else:
            assert len(devices) == 0

    def test_gpu_functions_repeated_calls(self):
        """Verify no crashes or leaks under repeated calls."""
        for _ in range(50):
            cfd_python.gpu_is_available()
            cfd_python.gpu_get_device_info()
            cfd_python.gpu_get_default_config()

    def test_gpu_select_device_invalid_id(self):
        """Test gpu_select_device with invalid device ID."""
        # If no GPU available, selecting any device should fail or be a no-op
        if not cfd_python.gpu_is_available():
            with pytest.raises((ValueError, RuntimeError)):
                cfd_python.gpu_select_device(9999)
        else:
            # With GPU, very high ID should fail
            devices = cfd_python.gpu_get_device_info()
            with pytest.raises((ValueError, RuntimeError)):
                cfd_python.gpu_select_device(len(devices) + 100)

    def test_gpu_functions_in_all(self):
        funcs = [
            "gpu_is_available",
            "gpu_get_device_info",
            "gpu_select_device",
            "gpu_get_default_config",
        ]
        for name in funcs:
            assert name in cfd_python.__all__, f"{name} not in __all__"
