"""
Tests for VTK output functions.

These tests verify that the VTK output functions handle memory correctly,
particularly the fixed use-after-free bug in write_vtk_vector.
"""

import os
import tempfile
import pytest


class TestWriteVtkScalar:
    """Test the write_vtk_scalar function."""

    def test_write_vtk_scalar_basic(self):
        """Test basic scalar VTK output."""
        import cfd_python

        nx, ny = 8, 8
        data = [float(i) for i in range(nx * ny)]

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "test_scalar.vtk")
            cfd_python.write_vtk_scalar(
                filename=filename,
                field_name="pressure",
                data=data,
                nx=nx, ny=ny,
                xmin=0.0, xmax=1.0,
                ymin=0.0, ymax=1.0
            )
            assert os.path.exists(filename)
            assert os.path.getsize(filename) > 0

    def test_write_vtk_scalar_with_floats(self):
        """Test scalar output with float values."""
        import cfd_python

        nx, ny = 5, 5
        data = [i * 0.1 for i in range(nx * ny)]

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "test_floats.vtk")
            cfd_python.write_vtk_scalar(
                filename=filename,
                field_name="temperature",
                data=data,
                nx=nx, ny=ny,
                xmin=0.0, xmax=2.0,
                ymin=0.0, ymax=2.0
            )
            assert os.path.exists(filename)

    def test_write_vtk_scalar_wrong_size_raises(self):
        """Test that wrong data size raises ValueError."""
        import cfd_python

        nx, ny = 8, 8
        # Wrong size: should be 64, we give 10
        data = [float(i) for i in range(10)]

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "test_wrong.vtk")
            with pytest.raises(ValueError):
                cfd_python.write_vtk_scalar(
                    filename=filename,
                    field_name="pressure",
                    data=data,
                    nx=nx, ny=ny,
                    xmin=0.0, xmax=1.0,
                    ymin=0.0, ymax=1.0
                )

    def test_write_vtk_scalar_repeated_calls(self):
        """Test repeated calls don't cause memory issues."""
        import cfd_python

        nx, ny = 10, 10
        data = [float(i) for i in range(nx * ny)]

        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(20):
                filename = os.path.join(tmpdir, f"test_{i}.vtk")
                cfd_python.write_vtk_scalar(
                    filename=filename,
                    field_name="density",
                    data=data,
                    nx=nx, ny=ny,
                    xmin=0.0, xmax=1.0,
                    ymin=0.0, ymax=1.0
                )
                assert os.path.exists(filename)


class TestWriteVtkVector:
    """Test the write_vtk_vector function.

    This specifically tests the code path with the fixed use-after-free bug
    where u_data and v_data pointers were not initialized to NULL.
    """

    def test_write_vtk_vector_basic(self):
        """Test basic vector VTK output."""
        import cfd_python

        nx, ny = 8, 8
        size = nx * ny
        u_data = [float(i) for i in range(size)]
        v_data = [float(i) * 0.5 for i in range(size)]

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "test_vector.vtk")
            cfd_python.write_vtk_vector(
                filename=filename,
                field_name="velocity",
                u_data=u_data,
                v_data=v_data,
                nx=nx, ny=ny,
                xmin=0.0, xmax=1.0,
                ymin=0.0, ymax=1.0
            )
            assert os.path.exists(filename)
            assert os.path.getsize(filename) > 0

    def test_write_vtk_vector_with_zeros(self):
        """Test vector output with zero values."""
        import cfd_python

        nx, ny = 5, 5
        size = nx * ny
        u_data = [0.0] * size
        v_data = [0.0] * size

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "test_zeros.vtk")
            cfd_python.write_vtk_vector(
                filename=filename,
                field_name="velocity",
                u_data=u_data,
                v_data=v_data,
                nx=nx, ny=ny,
                xmin=0.0, xmax=1.0,
                ymin=0.0, ymax=1.0
            )
            assert os.path.exists(filename)

    def test_write_vtk_vector_wrong_u_size_raises(self):
        """Test that wrong u_data size raises ValueError."""
        import cfd_python

        nx, ny = 8, 8
        size = nx * ny
        # Wrong size for u_data
        u_data = [float(i) for i in range(10)]
        v_data = [float(i) for i in range(size)]

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "test_wrong.vtk")
            with pytest.raises(ValueError):
                cfd_python.write_vtk_vector(
                    filename=filename,
                    field_name="velocity",
                    u_data=u_data,
                    v_data=v_data,
                    nx=nx, ny=ny,
                    xmin=0.0, xmax=1.0,
                    ymin=0.0, ymax=1.0
                )

    def test_write_vtk_vector_wrong_v_size_raises(self):
        """Test that wrong v_data size raises ValueError."""
        import cfd_python

        nx, ny = 8, 8
        size = nx * ny
        u_data = [float(i) for i in range(size)]
        # Wrong size for v_data
        v_data = [float(i) for i in range(10)]

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "test_wrong.vtk")
            with pytest.raises(ValueError):
                cfd_python.write_vtk_vector(
                    filename=filename,
                    field_name="velocity",
                    u_data=u_data,
                    v_data=v_data,
                    nx=nx, ny=ny,
                    xmin=0.0, xmax=1.0,
                    ymin=0.0, ymax=1.0
                )

    def test_write_vtk_vector_repeated_calls(self):
        """Test repeated calls don't cause memory issues (use-after-free regression)."""
        import cfd_python

        nx, ny = 10, 10
        size = nx * ny
        u_data = [float(i) for i in range(size)]
        v_data = [float(i) * 0.5 for i in range(size)]

        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(20):
                filename = os.path.join(tmpdir, f"test_{i}.vtk")
                cfd_python.write_vtk_vector(
                    filename=filename,
                    field_name="velocity",
                    u_data=u_data,
                    v_data=v_data,
                    nx=nx, ny=ny,
                    xmin=0.0, xmax=1.0,
                    ymin=0.0, ymax=1.0
                )
                assert os.path.exists(filename)

    def test_write_vtk_vector_large_grid(self):
        """Test vector output with larger grid."""
        import cfd_python

        nx, ny = 50, 50
        size = nx * ny
        u_data = [float(i % 100) for i in range(size)]
        v_data = [float((i * 2) % 100) for i in range(size)]

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "test_large.vtk")
            cfd_python.write_vtk_vector(
                filename=filename,
                field_name="velocity",
                u_data=u_data,
                v_data=v_data,
                nx=nx, ny=ny,
                xmin=0.0, xmax=1.0,
                ymin=0.0, ymax=1.0
            )
            assert os.path.exists(filename)
            # File should be substantial size
            assert os.path.getsize(filename) > 1000


class TestSetOutputDir:
    """Test the set_output_dir function."""

    def test_set_output_dir_basic(self):
        """Test setting output directory."""
        import cfd_python

        with tempfile.TemporaryDirectory() as tmpdir:
            # Should not raise
            cfd_python.set_output_dir(tmpdir)

    def test_set_output_dir_repeated(self):
        """Test setting output directory multiple times."""
        import cfd_python

        with tempfile.TemporaryDirectory() as tmpdir:
            for _ in range(10):
                cfd_python.set_output_dir(tmpdir)


class TestHasSolver:
    """Test the has_solver function."""

    def test_has_solver_existing(self):
        """Test has_solver returns True for existing solvers."""
        import cfd_python

        solvers = cfd_python.list_solvers()
        for solver in solvers:
            assert cfd_python.has_solver(solver) is True

    def test_has_solver_nonexistent(self):
        """Test has_solver returns False for nonexistent solver."""
        import cfd_python

        assert cfd_python.has_solver("nonexistent_solver_xyz") is False

    def test_has_solver_empty_string(self):
        """Test has_solver with empty string."""
        import cfd_python

        assert cfd_python.has_solver("") is False


class TestWriteCsvTimeseries:
    """Test the write_csv_timeseries function."""

    def test_write_csv_timeseries_basic(self):
        """Test basic CSV timeseries output."""
        import cfd_python

        nx, ny = 8, 8
        size = nx * ny
        u_data = [float(i) for i in range(size)]
        v_data = [float(i) * 0.5 for i in range(size)]
        p_data = [float(i) * 0.1 for i in range(size)]

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "timeseries.csv")
            cfd_python.write_csv_timeseries(
                filename=filename,
                step=0,
                time=0.0,
                u_data=u_data,
                v_data=v_data,
                p_data=p_data,
                nx=nx, ny=ny,
                dt=0.001,
                iterations=100,
                create_new=True
            )
            assert os.path.exists(filename)
            assert os.path.getsize(filename) > 0

    def test_write_csv_timeseries_append(self):
        """Test appending to CSV timeseries."""
        import cfd_python

        nx, ny = 5, 5
        size = nx * ny
        u_data = [float(i) for i in range(size)]
        v_data = [float(i) * 0.5 for i in range(size)]
        p_data = [float(i) * 0.1 for i in range(size)]

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "timeseries.csv")
            # Create new file
            cfd_python.write_csv_timeseries(
                filename=filename,
                step=0,
                time=0.0,
                u_data=u_data,
                v_data=v_data,
                p_data=p_data,
                nx=nx, ny=ny,
                dt=0.001,
                iterations=100,
                create_new=True
            )
            initial_size = os.path.getsize(filename)

            # Append to file
            cfd_python.write_csv_timeseries(
                filename=filename,
                step=1,
                time=0.001,
                u_data=u_data,
                v_data=v_data,
                p_data=p_data,
                nx=nx, ny=ny,
                dt=0.001,
                iterations=101,
                create_new=False
            )
            # File should be larger after append
            assert os.path.getsize(filename) > initial_size

    def test_write_csv_timeseries_repeated_calls(self):
        """Test repeated calls don't cause memory issues."""
        import cfd_python

        nx, ny = 8, 8
        size = nx * ny
        u_data = [float(i) for i in range(size)]
        v_data = [float(i) * 0.5 for i in range(size)]
        p_data = [float(i) * 0.1 for i in range(size)]

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "timeseries.csv")
            for step in range(20):
                cfd_python.write_csv_timeseries(
                    filename=filename,
                    step=step,
                    time=step * 0.001,
                    u_data=u_data,
                    v_data=v_data,
                    p_data=p_data,
                    nx=nx, ny=ny,
                    dt=0.001,
                    iterations=100 + step,
                    create_new=(step == 0)
                )


class TestInputValidation:
    """Test input validation doesn't cause crashes."""

    def test_vtk_scalar_non_float_in_list(self):
        """Test that non-float values in list are handled."""
        import cfd_python

        nx, ny = 4, 4
        # Mix of ints and floats - should be converted
        data = [i for i in range(nx * ny)]  # integers

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "test.vtk")
            # Should work - ints are convertible to float
            cfd_python.write_vtk_scalar(
                filename=filename,
                field_name="test",
                data=data,
                nx=nx, ny=ny,
                xmin=0.0, xmax=1.0,
                ymin=0.0, ymax=1.0
            )
            assert os.path.exists(filename)

    def test_vtk_scalar_invalid_type_raises(self):
        """Test that invalid types in list raise TypeError."""
        import cfd_python

        nx, ny = 4, 4
        # Strings are not convertible to float
        data = ["not", "a", "float"] + [0.0] * (nx * ny - 3)

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "test.vtk")
            with pytest.raises(TypeError):
                cfd_python.write_vtk_scalar(
                    filename=filename,
                    field_name="test",
                    data=data,
                    nx=nx, ny=ny,
                    xmin=0.0, xmax=1.0,
                    ymin=0.0, ymax=1.0
                )

    def test_csv_timeseries_non_list_u_raises(self):
        """Test that non-list u_data raises TypeError."""
        import cfd_python

        nx, ny = 4, 4
        size = nx * ny
        v_data = [0.0] * size
        p_data = [0.0] * size

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "test.csv")
            with pytest.raises(TypeError):
                cfd_python.write_csv_timeseries(
                    filename=filename,
                    step=0,
                    time=0.0,
                    u_data="not a list",  # Invalid type
                    v_data=v_data,
                    p_data=p_data,
                    nx=nx, ny=ny,
                    dt=0.001,
                    iterations=100,
                    create_new=True
                )

    def test_csv_timeseries_non_list_v_raises(self):
        """Test that non-list v_data raises TypeError."""
        import cfd_python

        nx, ny = 4, 4
        size = nx * ny
        u_data = [0.0] * size
        p_data = [0.0] * size

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "test.csv")
            with pytest.raises(TypeError):
                cfd_python.write_csv_timeseries(
                    filename=filename,
                    step=0,
                    time=0.0,
                    u_data=u_data,
                    v_data=(1, 2, 3),  # Tuple instead of list
                    p_data=p_data,
                    nx=nx, ny=ny,
                    dt=0.001,
                    iterations=100,
                    create_new=True
                )

    def test_csv_timeseries_non_list_p_raises(self):
        """Test that non-list p_data raises TypeError."""
        import cfd_python

        nx, ny = 4, 4
        size = nx * ny
        u_data = [0.0] * size
        v_data = [0.0] * size

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "test.csv")
            with pytest.raises(TypeError):
                cfd_python.write_csv_timeseries(
                    filename=filename,
                    step=0,
                    time=0.0,
                    u_data=u_data,
                    v_data=v_data,
                    p_data=None,  # None instead of list
                    nx=nx, ny=ny,
                    dt=0.001,
                    iterations=100,
                    create_new=True
                )

    def test_csv_timeseries_wrong_size_raises(self):
        """Test that wrong data size raises ValueError."""
        import cfd_python

        nx, ny = 4, 4
        size = nx * ny
        u_data = [0.0] * size
        v_data = [0.0] * size
        p_data = [0.0] * 5  # Wrong size

        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, "test.csv")
            with pytest.raises(ValueError):
                cfd_python.write_csv_timeseries(
                    filename=filename,
                    step=0,
                    time=0.0,
                    u_data=u_data,
                    v_data=v_data,
                    p_data=p_data,
                    nx=nx, ny=ny,
                    dt=0.001,
                    iterations=100,
                    create_new=True
                )
