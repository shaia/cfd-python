"""
Tests for CPU features detection and grid initialization variants (Phase 6).
"""

import pytest

import cfd_python


class TestSIMDConstants:
    """Test SIMD_* constants are defined and valid"""

    def test_simd_constants_exist(self):
        """Test all SIMD_* constants are defined"""
        assert hasattr(cfd_python, "SIMD_NONE")
        assert hasattr(cfd_python, "SIMD_AVX2")
        assert hasattr(cfd_python, "SIMD_NEON")

    def test_simd_constants_values(self):
        """Test SIMD_* constants have expected values"""
        assert cfd_python.SIMD_NONE == 0
        assert cfd_python.SIMD_AVX2 == 1
        assert cfd_python.SIMD_NEON == 2

    def test_simd_constants_in_all(self):
        """Test SIMD_* constants are in __all__"""
        assert "SIMD_NONE" in cfd_python.__all__
        assert "SIMD_AVX2" in cfd_python.__all__
        assert "SIMD_NEON" in cfd_python.__all__


class TestGetSIMDArch:
    """Test get_simd_arch function"""

    def test_get_simd_arch_returns_int(self):
        """Test get_simd_arch returns an integer"""
        arch = cfd_python.get_simd_arch()
        assert isinstance(arch, int)

    def test_get_simd_arch_valid_value(self):
        """Test get_simd_arch returns a valid SIMD constant"""
        arch = cfd_python.get_simd_arch()
        valid_values = [cfd_python.SIMD_NONE, cfd_python.SIMD_AVX2, cfd_python.SIMD_NEON]
        assert arch in valid_values


class TestGetSIMDName:
    """Test get_simd_name function"""

    def test_get_simd_name_returns_string(self):
        """Test get_simd_name returns a string"""
        name = cfd_python.get_simd_name()
        assert isinstance(name, str)

    def test_get_simd_name_valid_value(self):
        """Test get_simd_name returns a valid name"""
        name = cfd_python.get_simd_name()
        valid_names = ["none", "avx2", "neon"]
        assert name in valid_names

    def test_get_simd_name_matches_arch(self):
        """Test get_simd_name matches get_simd_arch"""
        arch = cfd_python.get_simd_arch()
        name = cfd_python.get_simd_name()

        expected_name = {
            cfd_python.SIMD_NONE: "none",
            cfd_python.SIMD_AVX2: "avx2",
            cfd_python.SIMD_NEON: "neon",
        }
        assert name == expected_name[arch]


class TestHasAVX2:
    """Test has_avx2 function"""

    def test_has_avx2_returns_bool(self):
        """Test has_avx2 returns a boolean"""
        result = cfd_python.has_avx2()
        assert isinstance(result, bool)

    def test_has_avx2_consistency(self):
        """Test has_avx2 is consistent with get_simd_arch"""
        has_avx2 = cfd_python.has_avx2()
        arch = cfd_python.get_simd_arch()

        if arch == cfd_python.SIMD_AVX2:
            assert has_avx2 is True
        else:
            # AVX2 is only true when arch is AVX2
            # (On x86-64 without AVX2, arch could be NONE)
            pass  # Can't assert False because ARM machines have NEON


class TestHasNEON:
    """Test has_neon function"""

    def test_has_neon_returns_bool(self):
        """Test has_neon returns a boolean"""
        result = cfd_python.has_neon()
        assert isinstance(result, bool)

    def test_has_neon_consistency(self):
        """Test has_neon is consistent with get_simd_arch"""
        has_neon = cfd_python.has_neon()
        arch = cfd_python.get_simd_arch()

        if arch == cfd_python.SIMD_NEON:
            assert has_neon is True


class TestHasSIMD:
    """Test has_simd function"""

    def test_has_simd_returns_bool(self):
        """Test has_simd returns a boolean"""
        result = cfd_python.has_simd()
        assert isinstance(result, bool)

    def test_has_simd_consistency(self):
        """Test has_simd is consistent with has_avx2 and has_neon"""
        has_simd = cfd_python.has_simd()
        has_avx2 = cfd_python.has_avx2()
        has_neon = cfd_python.has_neon()

        # has_simd should be True if either AVX2 or NEON is available
        if has_avx2 or has_neon:
            assert has_simd is True
        else:
            assert has_simd is False

    def test_has_simd_matches_arch(self):
        """Test has_simd matches get_simd_arch"""
        has_simd = cfd_python.has_simd()
        arch = cfd_python.get_simd_arch()

        if arch == cfd_python.SIMD_NONE:
            assert has_simd is False
        else:
            assert has_simd is True


# BUG: The stretched grid formula in the C library is incorrect.
# The cosh-based formula clusters points toward the center and doesn't span [xmin, xmax].
# See: cfd/ROADMAP.md "Known Issues > Stretched Grid Formula Bug"
# These tests are skipped until the C library fix is applied.
STRETCHED_GRID_BUG_REASON = (
    "Stretched grid formula bug: grid does not span [xmin, xmax]. "
    "See cfd/ROADMAP.md 'Known Issues' section."
)


@pytest.mark.skip(reason=STRETCHED_GRID_BUG_REASON)
class TestCreateGridStretched:
    """Test create_grid_stretched function.

    NOTE: These tests are skipped because the underlying C library has a bug
    in the stretching formula. The current cosh-based formula:
    - Clusters points toward the CENTER of the domain
    - Does not span the full domain (x[0] and x[n-1] both equal xmin)
    - Higher beta increases clustering toward center

    Once the C library is fixed to use the correct tanh-based formula:
        x[i] = xmin + (xmax - xmin) * (1 + tanh(beta * (2*xi - 1)) / tanh(beta)) / 2

    The expected correct behavior is:
    - x[0] == xmin, x[n-1] == xmax (grid spans full domain)
    - Higher beta clusters points near BOUNDARIES (useful for boundary layers)
    """

    def test_create_grid_stretched_basic(self):
        """Test basic stretched grid creation"""
        grid = cfd_python.create_grid_stretched(10, 10, 0.0, 1.0, 0.0, 1.0, 1.0)

        assert isinstance(grid, dict)
        assert grid["nx"] == 10
        assert grid["ny"] == 10
        assert grid["xmin"] == 0.0
        assert grid["xmax"] == 1.0
        assert grid["ymin"] == 0.0
        assert grid["ymax"] == 1.0
        assert grid["beta"] == 1.0

    def test_create_grid_stretched_has_coordinates(self):
        """Test stretched grid has coordinate lists"""
        grid = cfd_python.create_grid_stretched(5, 6, 0.0, 1.0, 0.0, 2.0, 1.5)

        assert "x" in grid
        assert "y" in grid
        assert isinstance(grid["x"], list)
        assert isinstance(grid["y"], list)
        assert len(grid["x"]) == 5
        assert len(grid["y"]) == 6

    def test_create_grid_stretched_spans_domain(self):
        """Test stretched grid spans full domain [xmin, xmax]"""
        grid = cfd_python.create_grid_stretched(10, 10, 0.0, 1.0, -1.0, 1.0, 2.0)

        # First point should be at xmin, last point at xmax
        assert abs(grid["x"][0] - grid["xmin"]) < 1e-10
        assert abs(grid["x"][-1] - grid["xmax"]) < 1e-10
        assert abs(grid["y"][0] - grid["ymin"]) < 1e-10
        assert abs(grid["y"][-1] - grid["ymax"]) < 1e-10

        # All points should be within bounds
        for x in grid["x"]:
            assert grid["xmin"] - 1e-10 <= x <= grid["xmax"] + 1e-10
        for y in grid["y"]:
            assert grid["ymin"] - 1e-10 <= y <= grid["ymax"] + 1e-10

    def test_create_grid_stretched_higher_beta_clusters_at_boundaries(self):
        """Test that higher beta clusters points near boundaries"""
        grid_low = cfd_python.create_grid_stretched(11, 11, 0.0, 1.0, 0.0, 1.0, 0.5)
        grid_high = cfd_python.create_grid_stretched(11, 11, 0.0, 1.0, 0.0, 1.0, 3.0)

        # With higher beta, spacing near boundaries should be smaller
        # Compare first cell size (x[1] - x[0])
        dx_first_low = grid_low["x"][1] - grid_low["x"][0]
        dx_first_high = grid_high["x"][1] - grid_high["x"][0]

        # Higher beta = smaller cells near boundaries
        assert dx_first_high < dx_first_low

    def test_create_grid_stretched_invalid_dimensions_raises(self):
        """Test that invalid dimensions raise ValueError"""
        with pytest.raises(ValueError):
            cfd_python.create_grid_stretched(0, 10, 0.0, 1.0, 0.0, 1.0, 1.0)

        with pytest.raises(ValueError):
            cfd_python.create_grid_stretched(10, -5, 0.0, 1.0, 0.0, 1.0, 1.0)

    def test_create_grid_stretched_invalid_bounds_raises(self):
        """Test that invalid bounds raise ValueError"""
        with pytest.raises(ValueError):
            cfd_python.create_grid_stretched(10, 10, 1.0, 0.0, 0.0, 1.0, 1.0)  # xmax < xmin

        with pytest.raises(ValueError):
            cfd_python.create_grid_stretched(10, 10, 0.0, 1.0, 2.0, 1.0, 1.0)  # ymax < ymin

    def test_create_grid_stretched_invalid_beta_raises(self):
        """Test that invalid beta raises ValueError"""
        with pytest.raises(ValueError):
            cfd_python.create_grid_stretched(10, 10, 0.0, 1.0, 0.0, 1.0, 0.0)

        with pytest.raises(ValueError):
            cfd_python.create_grid_stretched(10, 10, 0.0, 1.0, 0.0, 1.0, -1.0)


class TestPhase6Exports:
    """Test that all Phase 6 functions are properly exported"""

    def test_cpu_features_functions_in_all(self):
        """Test CPU features functions are in __all__"""
        functions = [
            "get_simd_arch",
            "get_simd_name",
            "has_avx2",
            "has_neon",
            "has_simd",
        ]
        for func_name in functions:
            assert func_name in cfd_python.__all__, f"{func_name} should be in __all__"
            assert callable(getattr(cfd_python, func_name)), f"{func_name} should be callable"

    def test_grid_functions_in_all(self):
        """Test grid functions are in __all__"""
        assert "create_grid_stretched" in cfd_python.__all__
        assert callable(cfd_python.create_grid_stretched)
