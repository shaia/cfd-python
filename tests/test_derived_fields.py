"""
Tests for derived fields and statistics API in cfd_python.
"""

import math

import pytest

import cfd_python


class TestCalculateFieldStats:
    """Test calculate_field_stats function"""

    def test_calculate_field_stats_basic(self):
        """Test basic statistics calculation"""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        stats = cfd_python.calculate_field_stats(data)

        assert isinstance(stats, dict)
        assert "min" in stats
        assert "max" in stats
        assert "avg" in stats
        assert "sum" in stats

        assert stats["min"] == 1.0
        assert stats["max"] == 5.0
        assert stats["avg"] == 3.0
        assert stats["sum"] == 15.0

    def test_calculate_field_stats_single_value(self):
        """Test statistics with single value"""
        data = [42.0]
        stats = cfd_python.calculate_field_stats(data)

        assert stats["min"] == 42.0
        assert stats["max"] == 42.0
        assert stats["avg"] == 42.0
        assert stats["sum"] == 42.0

    def test_calculate_field_stats_negative_values(self):
        """Test statistics with negative values"""
        data = [-5.0, -2.0, 0.0, 2.0, 5.0]
        stats = cfd_python.calculate_field_stats(data)

        assert stats["min"] == -5.0
        assert stats["max"] == 5.0
        assert stats["avg"] == 0.0
        assert stats["sum"] == 0.0

    def test_calculate_field_stats_large_field(self):
        """Test statistics with larger field"""
        nx, ny = 10, 10
        data = [float(i) for i in range(nx * ny)]
        stats = cfd_python.calculate_field_stats(data)

        assert stats["min"] == 0.0
        assert stats["max"] == 99.0
        assert abs(stats["avg"] - 49.5) < 1e-10
        assert stats["sum"] == 4950.0

    def test_calculate_field_stats_empty_raises(self):
        """Test that empty list raises ValueError"""
        with pytest.raises(ValueError):
            cfd_python.calculate_field_stats([])

    def test_calculate_field_stats_wrong_type_raises(self):
        """Test that non-list raises TypeError"""
        with pytest.raises(TypeError):
            cfd_python.calculate_field_stats("not a list")


class TestComputeVelocityMagnitude:
    """Test compute_velocity_magnitude function"""

    def test_compute_velocity_magnitude_basic(self):
        """Test basic velocity magnitude computation"""
        nx, ny = 2, 2
        u = [3.0, 0.0, 0.0, 4.0]
        v = [4.0, 1.0, 0.0, 3.0]

        result = cfd_python.compute_velocity_magnitude(u, v, nx, ny)

        assert isinstance(result, list)
        assert len(result) == nx * ny
        # sqrt(3^2 + 4^2) = 5
        assert abs(result[0] - 5.0) < 1e-10
        # sqrt(0^2 + 1^2) = 1
        assert abs(result[1] - 1.0) < 1e-10
        # sqrt(0^2 + 0^2) = 0
        assert abs(result[2] - 0.0) < 1e-10
        # sqrt(4^2 + 3^2) = 5
        assert abs(result[3] - 5.0) < 1e-10

    def test_compute_velocity_magnitude_uniform(self):
        """Test with uniform velocity field"""
        nx, ny = 4, 4
        u = [1.0] * (nx * ny)
        v = [1.0] * (nx * ny)

        result = cfd_python.compute_velocity_magnitude(u, v, nx, ny)

        # sqrt(1^2 + 1^2) = sqrt(2)
        expected = math.sqrt(2.0)
        for val in result:
            assert abs(val - expected) < 1e-10

    def test_compute_velocity_magnitude_zero_field(self):
        """Test with zero velocity field"""
        nx, ny = 3, 3
        u = [0.0] * (nx * ny)
        v = [0.0] * (nx * ny)

        result = cfd_python.compute_velocity_magnitude(u, v, nx, ny)

        for val in result:
            assert val == 0.0

    def test_compute_velocity_magnitude_size_mismatch_raises(self):
        """Test that mismatched sizes raise ValueError"""
        nx, ny = 4, 4
        u = [1.0] * 16
        v = [1.0] * 8  # Wrong size

        with pytest.raises(ValueError):
            cfd_python.compute_velocity_magnitude(u, v, nx, ny)

    def test_compute_velocity_magnitude_wrong_type_raises(self):
        """Test that non-list raises TypeError"""
        with pytest.raises(TypeError):
            cfd_python.compute_velocity_magnitude("not list", [1.0], 1, 1)


class TestComputeFlowStatistics:
    """Test compute_flow_statistics function"""

    def test_compute_flow_statistics_basic(self):
        """Test basic flow statistics computation"""
        nx, ny = 2, 2
        u = [1.0, 2.0, 3.0, 4.0]
        v = [0.5, 1.0, 1.5, 2.0]
        p = [100.0, 101.0, 102.0, 103.0]

        result = cfd_python.compute_flow_statistics(u, v, p, nx, ny)

        assert isinstance(result, dict)
        assert "u" in result
        assert "v" in result
        assert "p" in result
        assert "velocity_magnitude" in result

        # Check u stats
        assert result["u"]["min"] == 1.0
        assert result["u"]["max"] == 4.0
        assert result["u"]["avg"] == 2.5
        assert result["u"]["sum"] == 10.0

        # Check v stats
        assert result["v"]["min"] == 0.5
        assert result["v"]["max"] == 2.0
        assert result["v"]["avg"] == 1.25
        assert result["v"]["sum"] == 5.0

        # Check p stats
        assert result["p"]["min"] == 100.0
        assert result["p"]["max"] == 103.0
        assert result["p"]["avg"] == 101.5
        assert result["p"]["sum"] == 406.0

    def test_compute_flow_statistics_velocity_magnitude_included(self):
        """Test that velocity magnitude stats are computed"""
        nx, ny = 2, 2
        u = [3.0, 0.0, 0.0, 4.0]
        v = [4.0, 0.0, 0.0, 3.0]
        p = [0.0, 0.0, 0.0, 0.0]

        result = cfd_python.compute_flow_statistics(u, v, p, nx, ny)

        vel_mag = result["velocity_magnitude"]
        # vel_mag values: [5.0, 0.0, 0.0, 5.0]
        assert vel_mag["min"] == 0.0
        assert vel_mag["max"] == 5.0
        assert vel_mag["avg"] == 2.5
        assert vel_mag["sum"] == 10.0

    def test_compute_flow_statistics_size_mismatch_raises(self):
        """Test that mismatched sizes raise ValueError"""
        nx, ny = 4, 4
        u = [1.0] * 16
        v = [1.0] * 16
        p = [1.0] * 8  # Wrong size

        with pytest.raises(ValueError):
            cfd_python.compute_flow_statistics(u, v, p, nx, ny)

    def test_compute_flow_statistics_wrong_type_raises(self):
        """Test that non-list raises TypeError"""
        with pytest.raises(TypeError):
            cfd_python.compute_flow_statistics([1.0], "not list", [1.0], 1, 1)


class TestDerivedFieldsExported:
    """Test that all derived fields functions are properly exported"""

    def test_functions_in_all(self):
        """Test all derived fields functions are in __all__"""
        functions = [
            "calculate_field_stats",
            "compute_velocity_magnitude",
            "compute_flow_statistics",
        ]
        for func_name in functions:
            assert func_name in cfd_python.__all__, f"{func_name} should be in __all__"
            assert callable(getattr(cfd_python, func_name)), f"{func_name} should be callable"
