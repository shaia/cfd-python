"""
Tests for VTK and CSV output functions
"""

import pytest

import cfd_python


class TestVTKOutput:
    """Test VTK output functions"""

    def test_write_vtk_scalar(self, tmp_path):
        """Test write_vtk_scalar creates file"""
        output_file = tmp_path / "scalar_field.vtk"
        nx, ny = 5, 5
        data = [float(i) for i in range(nx * ny)]

        cfd_python.write_vtk_scalar(
            str(output_file), "test_field", data, nx, ny, 0.0, 1.0, 0.0, 1.0
        )

        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_write_vtk_scalar_validates_size(self, tmp_path):
        """Test write_vtk_scalar validates data size"""
        output_file = tmp_path / "test.vtk"
        with pytest.raises(ValueError):
            cfd_python.write_vtk_scalar(
                str(output_file),
                "test",
                [1.0, 2.0, 3.0],  # 3 elements
                5,
                5,
                0.0,
                1.0,
                0.0,
                1.0,  # expects 25 elements
            )

    def test_write_vtk_vector(self, tmp_path):
        """Test write_vtk_vector creates file"""
        output_file = tmp_path / "vector_field.vtk"
        nx, ny = 5, 5
        u_data = [float(i) for i in range(nx * ny)]
        v_data = [float(i) * 0.5 for i in range(nx * ny)]

        cfd_python.write_vtk_vector(
            str(output_file), "velocity", u_data, v_data, nx, ny, 0.0, 1.0, 0.0, 1.0
        )

        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_write_vtk_vector_validates_size(self, tmp_path):
        """Test write_vtk_vector validates data sizes"""
        output_file = tmp_path / "test.vtk"
        with pytest.raises(ValueError):
            cfd_python.write_vtk_vector(
                str(output_file),
                "test",
                [1.0, 2.0],  # 2 elements
                [1.0, 2.0, 3.0],  # 3 elements
                5,
                5,
                0.0,
                1.0,
                0.0,
                1.0,
            )


class TestCSVOutput:
    """Test CSV output functions"""

    def test_write_csv_timeseries_creates_file(self, tmp_path):
        """Test write_csv_timeseries creates file"""
        output_file = tmp_path / "timeseries.csv"
        nx, ny = 5, 5
        size = nx * ny
        u_data = [0.1] * size
        v_data = [0.05] * size
        p_data = [1.0] * size

        cfd_python.write_csv_timeseries(
            str(output_file),
            step=0,
            time=0.0,
            u_data=u_data,
            v_data=v_data,
            p_data=p_data,
            nx=nx,
            ny=ny,
            dt=0.001,
            iterations=10,
            create_new=True,
        )

        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_write_csv_timeseries_append(self, tmp_path):
        """Test write_csv_timeseries can append to file"""
        output_file = tmp_path / "timeseries_append.csv"
        nx, ny = 3, 3
        size = nx * ny
        u_data = [0.1] * size
        v_data = [0.05] * size
        p_data = [1.0] * size

        # Create new file
        cfd_python.write_csv_timeseries(
            str(output_file),
            step=0,
            time=0.0,
            u_data=u_data,
            v_data=v_data,
            p_data=p_data,
            nx=nx,
            ny=ny,
            dt=0.001,
            iterations=10,
            create_new=True,
        )
        initial_size = output_file.stat().st_size

        # Append to file
        cfd_python.write_csv_timeseries(
            str(output_file),
            step=1,
            time=0.001,
            u_data=u_data,
            v_data=v_data,
            p_data=p_data,
            nx=nx,
            ny=ny,
            dt=0.001,
            iterations=10,
            create_new=False,
        )

        # File should be larger after append
        assert output_file.stat().st_size > initial_size


class TestSetOutputDir:
    """Test set_output_dir function"""

    def test_set_output_dir_accepts_string(self, tmp_path):
        """Test set_output_dir accepts a path string"""
        cfd_python.set_output_dir(str(tmp_path))

    def test_set_output_dir_returns_none(self, tmp_path):
        """Test set_output_dir returns None"""
        result = cfd_python.set_output_dir(str(tmp_path))
        assert result is None
