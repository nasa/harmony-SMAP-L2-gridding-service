"""Tests for grid module."""

from pathlib import Path
from unittest.mock import call

import numpy as np
import pytest
import xarray as xr
from xarray import DataArray, DataTree

from smap_l2_gridder import grid
from smap_l2_gridder.grid import (
    InvalidCollectionError,
    default_fill_value,
    get_dataset_shortname,
    get_grid_information,
    get_target_grid_information,
    grid_variable,
    locate_row_and_column_in_node,
    prepare_variable,
    process_input,
    spl2smap_index_locator,
    transfer_metadata,
    variable_fill_value,
)


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
    out_file = tmp_path / 'output.nc'
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
    sample_datatree['Metadata/testing'] = additional_metadata

    out_dt = transfer_metadata(sample_datatree, out_dt)
    assert (
        out_dt['Metadata/Lineage/DEMSLP'].attrs['Description']
        == 'Representative surface slope data for each of the 9 km cells'
    )
    assert out_dt['Metadata/testing'].attrs == test_metadata


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


@pytest.mark.parametrize('sample_datatree', ['sample_SPL2SMP_E_file'], indirect=True)
def test_get_grid_information(sample_datatree, mocker):
    """Verify correct information is returned as grid_info for SPL2SMP_E data."""
    target_grid_info = mocker.patch('smap_l2_gridder.grid.get_target_grid_information')

    for node in ['Soil_Moisture_Retrieval_Data_Polar', 'Soil_Moisture_Retrieval_Data']:
        short_name = 'SPL2SMP_E'
        actual_grid_info = get_grid_information(sample_datatree, node, short_name)
        np.testing.assert_array_almost_equal(
            actual_grid_info['src']['rows'], sample_datatree[f'{node}/EASE_row_index']
        )
        np.testing.assert_array_almost_equal(
            actual_grid_info['src']['cols'],
            sample_datatree[f'{node}/EASE_column_index'],
        )
        target_grid_info.assert_called_with(node, short_name)


@pytest.mark.parametrize(
    'node,stem,expected',
    [
        ('SPL2SMAP', 'EASE_column_index', 'SPL2SMAP/EASE_column_index'),
        ('node_3km', 'EASE_column_index', 'node_3km/EASE_column_index_3km'),
        ('SPL2SMAP', 'EASE_row_index', 'SPL2SMAP/EASE_row_index'),
        ('SPL2SMAP_3km', 'EASE_row_index', 'SPL2SMAP_3km/EASE_row_index_3km'),
    ],
)
def test_spl2smap_index_locator(node, stem, expected):
    """Validate index locator for SPL2SMAP."""
    assert spl2smap_index_locator(node, stem) == expected


@pytest.mark.parametrize('sample_datatree', ['sample_SPL2SMAP_file'], indirect=True)
@pytest.mark.parametrize(
    'node,suffix',
    [
        ('Soil_Moisture_Retrieval_Data_3km', '_3km'),
        ('Soil_Moisture_Retrieval_Data', ''),
    ],
)
def test_get_grid_information_spl2smap(sample_datatree, node, suffix, mocker):
    """Verify correct information is returned as grid_info for SPL2SMAP data."""
    target_grid_info = mocker.patch('smap_l2_gridder.grid.get_target_grid_information')

    expected_short_name = 'SPL2SMAP'
    short_name = get_dataset_shortname(sample_datatree)

    actual_grid_info = get_grid_information(sample_datatree, node, short_name)

    np.testing.assert_array_almost_equal(
        actual_grid_info['src']['rows'],
        sample_datatree[f'{node}/EASE_row_index{suffix}'],
    )
    np.testing.assert_array_almost_equal(
        actual_grid_info['src']['cols'],
        sample_datatree[f'{node}/EASE_column_index{suffix}'],
    )
    target_grid_info.assert_called_with(node, expected_short_name)


def test_locate_row_and_column_in_node_SPL2SMP_E(mocker):
    """Tests SPL2SMP_E collection."""
    locator_patch = mocker.patch('smap_l2_gridder.grid.spl2smap_index_locator')
    mock_dt = mocker.Mock()
    mock_dt.__getitem__ = mocker.Mock()

    row, col = locate_row_and_column_in_node(mock_dt, 'node', 'SPL2SMP_E')
    mock_dt.__getitem__.assert_has_calls(
        [call('node/EASE_row_index'), call('node/EASE_column_index')]
    )
    locator_patch.assert_not_called


def test_locate_row_and_column_in_node_SPL2SMAP(mocker):
    """Tests SPL2SMAP collection."""
    locator_spy = mocker.spy(grid, 'spl2smap_index_locator')
    mock_dt = mocker.Mock()
    mock_dt.__getitem__ = mocker.Mock()
    node = 'nodename_3km'

    row, col = locate_row_and_column_in_node(mock_dt, node, 'SPL2SMAP')
    mock_dt.__getitem__.assert_has_calls(
        [call(f'{node}/EASE_row_index_3km'), call(f'{node}/EASE_column_index_3km')]
    )
    locator_spy.assert_has_calls(
        [call(node, 'EASE_row_index'), call(node, 'EASE_column_index')]
    )


def test_locate_row_and_column_in_node_bad_short_name(mocker):
    """Check that unimplemented collection raises exception."""
    locator_patch = mocker.patch('smap_l2_gridder.grid.spl2smap_index_locator')
    mock_dt = mocker.Mock()
    getitem_mock = mocker.Mock()
    mock_dt.__getitem__ = getitem_mock

    short_name = 'MADEUP_SHORTNAME'
    with pytest.raises(InvalidCollectionError, match=f'.*{short_name}.*'):
        locate_row_and_column_in_node(None, 'node_name', short_name)

    locator_patch.assert_not_called
    getitem_mock.assert_not_called


def test_get_target_grid_information(mocker):
    """Test that the node name correctly identifies which gpd file to parse."""
    parse_gpd_file_mock = mocker.patch('smap_l2_gridder.grid.parse_gpd_file')

    get_target_grid_information('any-node-name', 'SPL2SMP_E')
    parse_gpd_file_mock.assert_called_with('EASE2_M09km.gpd')

    get_target_grid_information('any-node-name_Polar', 'SPL2SMP_E')
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
