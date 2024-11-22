"""Tests for grid module."""

from pathlib import Path

import numpy as np
import pytest
import xarray as xr
from xarray import DataArray, DataTree

from smap_l2_gridder.grid import (
    default_fill_value,
    get_grid_information,
    get_target_grid_information,
    grid_variable,
    prepare_variable,
    process_input,
    transfer_metadata,
    variable_fill_value,
)


# Fixtures
@pytest.fixture
def sample_datatree(tmp_path):
    """Create a sample DataTree for testing.

    It is round tripped to a temporary disk location for easy of setting the
    correct NetCDF attributes.

    This represents the expected shape of an SPL2SMP_E granule.
    The data is repeated for both global and polar nodes.

    """
    dt = DataTree()
    dt["Metadata/Lineage/DEMSLP"] = DataTree()
    dt["Metadata/Lineage/DEMSLP"].attrs[
        "Description"
    ] = "Representative surface slope data for each of the 9 km cells"

    nodes = ["Soil_Moisture_Retrieval_Data", "Soil_Moisture_Retrieval_Data_Polar"]
    for node in nodes:
        dt[f"{node}"] = DataTree()
        dt[f"{node}/EASE_column_index"] = DataArray(
            data=np.array([1175, 1175, 1175, 1175, 1175], dtype=np.uint16),
            dims=["phony_dim_0"],
            name="EASE_column_index",
            attrs={
                "long_name": "The column index of the 9 km EASE grid cell...",
                "valid_min": 0,
                "valid_max": 3855,
                "_FillValue": np.uint16(65534),
            },
        )

        dt[f"{node}/EASE_row_index"] = DataArray(
            data=np.array([1603, 1604, 1605, 1606, 1607], dtype=np.uint16),
            dims=["phony_dim_0"],
            attrs={
                "long_name": "The row index of the 9 km EASE grid cell...",
                "valid_min": 0,
                "valid_max": 1623,
                "_FillValue": np.uint16(65534),
            },
        )

        dt[f'{node}/albedo'] = DataArray(
            data=np.array(
                [0.0009434, 0.00136986, 0.0025, 0.0, -9999.0], dtype=np.float32
            ),
            dims=['phony_dim_0'],
            attrs={
                'long_name': 'Diffuse reflecting power of the Earth&apos;s...',
                'valid_min': 0.0,
                'valid_max': 1.0,
                '_FillValue': np.float32(-9999.0),
            },
        )

        # This part of the fixture REALLY slow. Including it adds 7 seconds!!
        # to the run time of the pytests and there is only a single test that
        # needs this.  I tested this function outside of pytest and it's not
        # acting like a bottle neck so I'm not sure what to do. But for now
        # I'll remove this and skip the test.

        # dt[f'{node}/tb_time_utc'] = DataArray(
        #     data=np.array(
        #         [
        #             '2024-11-06T03:59:27.313Z',
        #             '2024-11-06T03:59:25.754Z',
        #             '2024-11-06T03:59:24.374Z',
        #             '2024-11-06T03:59:22.735Z',
        #             '2024-11-06T03:59:21.191Z',
        #         ],
        #         dtype='<U24',
        #     ),
        #     dims=['phony_dim_0'],
        #     attrs={'long_name': 'Arithmetic average of the acquisition time...'},
        # )

    # Round trip this to a file so that the encoding values are what we see
    # when we read from a NetCDF file.
    tmp_file = tmp_path / 'tmp_output.nc'
    dt.to_netcdf(tmp_file)
    dt2 = xr.open_datatree(tmp_file, decode_times=False)
    return dt2


@pytest.fixture
def sample_grid_info():
    """Create sample grid information dictionary."""
    return {
        'src': {
            'rows': DataArray(np.array([0, 1, 2, 3, 4])),
            'cols': DataArray(np.array([0, 1, 2, 3, 4])),
        },
        'target': {'Grid Height': 5, 'Grid Width': 5, 'wkt': 'DUMMY WKT'},
    }


# Tests below
# ----------
def test_process_input(sample_datatree, tmp_path):
    """Test process_input function.

    This processes the sample_datatree and then verifies the file was written
    as well as some of the metadata was generated properly.

    """
    out_file = tmp_path / "output.nc"
    process_input(sample_datatree, out_file)
    assert Path(out_file).exists()
    out_dt = xr.open_datatree(out_file)
    assert (
        out_dt['Metadata/Lineage/DEMSLP'].attrs['Description']
        == 'Representative surface slope data for each of the 9 km cells'
    )
    assert out_dt['Soil_Moisture_Retrieval_Data/albedo'].dims == ('y-dim', 'x-dim')
    assert (
        out_dt['Soil_Moisture_Retrieval_Data_Polar/crs'].attrs['projected_crs_name']
        == 'WGS 84 / NSIDC EASE-Grid 2.0 North'
    )
    assert (
        out_dt['Soil_Moisture_Retrieval_Data/crs'].attrs['projected_crs_name']
        == 'WGS 84 / NSIDC EASE-Grid 2.0 Global'
    )


def test_transfer_metadata(sample_datatree):
    """Test metadata transfer for multiple groups."""
    out_dt = DataTree()
    test_metadata = {'size': 3.5, 'age': 23, 'processing': 'complete'}
    additional_metadata = DataTree()
    additional_metadata.attrs = test_metadata
    sample_datatree["Metadata/testing"] = additional_metadata

    out_dt = transfer_metadata(sample_datatree, out_dt)
    assert (
        out_dt['Metadata/Lineage/DEMSLP'].attrs['Description']
        == 'Representative surface slope data for each of the 9 km cells'
    )
    assert out_dt["Metadata/testing"].attrs == test_metadata


def test_prepare_variable_albedo(sample_datatree, sample_grid_info):
    """Test prepare_variable function.

    sample_grid_info puts the input vector into the diagonal starting at 0,0

    """
    var = sample_datatree['Soil_Moisture_Retrieval_Data/albedo']
    result = prepare_variable(var, sample_grid_info)

    assert isinstance(result, DataArray)
    assert result.dims == ('y-dim', 'x-dim')
    for i in range(4):
        assert result[i, i] == var[i]
    assert result[4, 4] == -9999.0
    assert result.encoding['_FillValue'] == -9999.0
    assert 'zlib' in result.encoding
    assert 'complevel' in result.encoding
    assert result.attrs['grid_mapping'] == 'crs'


def test_prepare_variable_encoding_of_utc_time(sample_datatree, sample_grid_info):
    """Test string variables don't get compression encoding."""
    var = sample_datatree['Soil_Moisture_Retrieval_Data/EASE_column_index']
    var.name = 'tb_time_utc'
    result = prepare_variable(var, sample_grid_info)

    assert isinstance(result, DataArray)
    assert result.dims == ('y-dim', 'x-dim')
    for i in range(5):
        assert result[i, i] == var[i]

    assert result.encoding['_FillValue'] == np.uint16(65534)
    assert 'zlib' not in result.encoding
    assert 'complevel' not in result.encoding
    assert result.attrs['grid_mapping'] == 'crs'


def test_get_grid_information(sample_datatree, mocker):
    """Verify correct information is returned as grid_info."""
    target_grid_info = mocker.patch('smap_l2_gridder.grid.get_target_grid_information')
    node = "Soil_Moisture_Retrieval_Data_Polar"

    actual_grid_info = get_grid_information(sample_datatree, node)
    np.testing.assert_array_almost_equal(
        actual_grid_info['src']['rows'], sample_datatree[f'{node}/EASE_row_index']
    )
    np.testing.assert_array_almost_equal(
        actual_grid_info['src']['cols'], sample_datatree[f'{node}/EASE_column_index']
    )
    target_grid_info.assert_called_with(f'{node}')


def test_get_target_grid_information(mocker):
    """Test that the node name correctly identifies the gpd file to parse."""
    parse_gpd_file_mock = mocker.patch('smap_l2_gridder.grid.parse_gpd_file')

    get_target_grid_information("any-node-name")
    parse_gpd_file_mock.assert_called_with('EASE2_M09km.gpd')

    get_target_grid_information("any-node-name_Polar")
    parse_gpd_file_mock.assert_called_with('EASE2_N09km.gpd')


def test_grid_variable(sample_datatree, sample_grid_info):
    """Test grid_variable function."""
    var = sample_datatree['Soil_Moisture_Retrieval_Data_Polar/EASE_column_index']
    result = grid_variable(var, sample_grid_info)

    expected_column = np.full((5, 5), np.uint16(65534))
    # The row/col is just the diagonal values.
    for idx in range(len(var)):
        expected_column[idx, idx] = var.data[idx]

    assert isinstance(result, DataArray)
    assert result.dims == ('y-dim', 'x-dim')
    assert result.shape == (5, 5)
    np.testing.assert_array_almost_equal(expected_column, result)


@pytest.mark.skip('Slow fixture')
def test_grid_variable_string(sample_datatree, sample_grid_info):
    """Test grid_variable function."""
    var = sample_datatree['Soil_Moisture_Retrieval_Data_Polar/tb_time_utc']
    result = grid_variable(var, sample_grid_info)

    expected_utc = np.full((5, 5), 'None').astype('<U24')

    # The row/col is just the diagonal values.
    for idx in range(len(var)):
        expected_utc[idx, idx] = var.data[idx]

    assert isinstance(result, DataArray)
    assert result.dims == ('y-dim', 'x-dim')
    assert result.shape == (5, 5)
    # There is a problem comparing the arrays directly with
    # np.testing.assert_arrays_equal (mixed data type promotion?). So just
    # iterate over every value and and compare them directly.
    for actual, expected in zip(np.nditer(result.data), np.nditer(expected_utc)):
        assert actual == expected, f'full comparison {result.data}\n{expected_utc}'


def test_variable_fill_value(mocker):
    """Test variable_fill_value function."""
    # Test with _FillValue in encoding
    var = DataArray([1], attrs={'_FillValue': -999.9})
    var.encoding = {'_FillValue': -99.99}
    assert variable_fill_value(var) == -99.99

    # Test with _FillValue in attrs
    var = DataArray([1], attrs={'_FillValue': -999.9})
    assert variable_fill_value(var) == -999.9

    # Test with missing_value
    var = DataArray([1], attrs={'missing_value': -9999})
    assert variable_fill_value(var) == -9999

    var = DataArray(['z'])
    var.encoding['dtype'] = '<U1'
    default_fill_value_mock = mocker.patch('smap_l2_gridder.grid.default_fill_value')
    default_fill_value_mock.return_value = None
    assert variable_fill_value(var) is None
    default_fill_value_mock.assert_called_with('<U1')


def test_default_fill_value():
    """Test default_fill_value function."""
    # Test float
    assert default_fill_value(np.dtype('float32')) == np.float32(-9999.0)
    assert default_fill_value(np.dtype('float64')) == np.float32(-9999.0)
    assert default_fill_value(np.dtype('uint16')) == np.uint16(65535)
    assert default_fill_value(np.dtype('int16')) == np.int16(32767)
    assert default_fill_value(np.dtype('str')) is None
