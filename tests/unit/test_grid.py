"""Tests for grid module."""

from pathlib import Path
from unittest.mock import call

import numpy as np
import pytest
import xarray as xr
from xarray import DataArray, DataTree

from smap_l2_gridder import grid
from smap_l2_gridder.exceptions import InvalidCollectionError, InvalidVariableShape
from smap_l2_gridder.grid import (
    default_fill_value,
    flatten_2d_data,
    get_collection_shortname,
    get_grid_information,
    get_target_grid_information,
    grid_variable,
    is_compressible,
    locate_row_and_column_for_group,
    prepare_variable,
    process_input,
    split_2d_variable,
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
    tb_time_utc = DataArray(
        data=np.array(
            [
                '2024-11-06T03:59:27.313Z',
                '2024-11-06T03:59:25.754Z',
                '2024-11-06T03:59:24.374Z',
                '2024-11-06T03:59:22.735Z',
                '2024-11-06T03:59:21.191Z',
            ],
            dtype='<U24',
        ),
        dims=['phony_dim_0'],
        attrs={'long_name': 'Arithmetic average of the acquisition time...'},
    )

    result = prepare_variable(tb_time_utc, sample_grid_info)

    assert isinstance(result, DataArray)
    assert result.dims == ('y-dim', 'x-dim')
    for i in range(5):
        assert result[i, i] == tb_time_utc[i]

    assert result.encoding['_FillValue'] is None
    assert 'zlib' not in result.encoding
    assert 'complevel' not in result.encoding
    assert result.attrs['grid_mapping'] == 'crs'


@pytest.mark.parametrize('sample_datatree', ['sample_SPL2SMP_E_file'], indirect=True)
def test_get_grid_information(sample_datatree, mocker):
    """Verify correct information is returned as grid_info for SPL2SMP_E data."""
    target_grid_info = mocker.patch('smap_l2_gridder.grid.get_target_grid_information')

    for group in ['Soil_Moisture_Retrieval_Data_Polar', 'Soil_Moisture_Retrieval_Data']:
        short_name = 'SPL2SMP_E'
        actual_grid_info = get_grid_information(sample_datatree, group, short_name)
        np.testing.assert_array_almost_equal(
            actual_grid_info['src']['rows'], sample_datatree[f'{group}/EASE_row_index']
        )
        np.testing.assert_array_almost_equal(
            actual_grid_info['src']['cols'],
            sample_datatree[f'{group}/EASE_column_index'],
        )
        target_grid_info.assert_called_with(group, short_name)


@pytest.mark.parametrize('sample_datatree', ['sample_SPL2SMAP_file'], indirect=True)
@pytest.mark.parametrize(
    'group,suffix',
    [
        ('Soil_Moisture_Retrieval_Data_3km', '_3km'),
        ('Soil_Moisture_Retrieval_Data', ''),
    ],
)
def test_get_grid_information_spl2smap(sample_datatree, group, suffix, mocker):
    """Verify correct information is returned as grid_info for SPL2SMAP data."""
    target_grid_info = mocker.patch('smap_l2_gridder.grid.get_target_grid_information')

    expected_short_name = 'SPL2SMAP'
    short_name = get_collection_shortname(sample_datatree)

    actual_grid_info = get_grid_information(sample_datatree, group, short_name)

    np.testing.assert_array_almost_equal(
        actual_grid_info['src']['rows'],
        sample_datatree[f'{group}/EASE_row_index{suffix}'],
    )
    np.testing.assert_array_almost_equal(
        actual_grid_info['src']['cols'],
        sample_datatree[f'{group}/EASE_column_index{suffix}'],
    )
    target_grid_info.assert_called_with(group, expected_short_name)


def test_locate_row_and_column_for_group_SPL2SMP_E(mocker):
    """Tests SPL2SMP_E collection."""
    mock_dt = mocker.Mock()
    mock_dt.__getitem__ = mocker.Mock()

    row, col = locate_row_and_column_for_group(
        mock_dt, 'Soil_Moisture_Retrieval_Data', 'SPL2SMP_E'
    )
    mock_dt.__getitem__.assert_has_calls(
        [
            call('Soil_Moisture_Retrieval_Data/EASE_row_index'),
            call('Soil_Moisture_Retrieval_Data/EASE_column_index'),
        ]
    )


def test_locate_row_and_column_for_group_SPL2SMAP(mocker):
    """Tests SPL2SMAP collection."""
    mock_dt = mocker.Mock()
    mock_dt.__getitem__ = mocker.Mock()
    group = 'Soil_Moisture_Retrieval_Data_3km'

    row, col = locate_row_and_column_for_group(mock_dt, group, 'SPL2SMAP')
    mock_dt.__getitem__.assert_has_calls(
        [call(f'{group}/EASE_row_index_3km'), call(f'{group}/EASE_column_index_3km')]
    )


def test_locate_row_and_column_for_group_bad_short_name(mocker):
    """Check that unimplemented collection raises exception."""
    mock_dt = mocker.Mock()
    getitem_mock = mocker.Mock()
    mock_dt.__getitem__ = getitem_mock

    short_name = 'MADEUP_SHORTNAME'
    with pytest.raises(InvalidCollectionError, match=f'.*{short_name}.*'):
        locate_row_and_column_for_group(None, 'group_name', short_name)

    getitem_mock.assert_not_called


@pytest.mark.parametrize(
    'group,short_name,expected',
    [
        ('Soil_Moisture_Retrieval_Data', 'SPL2SMP_E', 'EASE2_M09km.gpd'),
        ('Soil_Moisture_Retrieval_Data_Polar', 'SPL2SMP_E', 'EASE2_N09km.gpd'),
        ('Soil_Moisture_Retrieval_Data', 'SPL2SMAP', 'EASE2_M09km.gpd'),
        ('Soil_Moisture_Retrieval_Data_3km', 'SPL2SMAP', 'EASE2_M03km.gpd'),
    ],
)
def test_get_target_grid_information(group, short_name, expected, mocker):
    """Test that the group name correctly identifies which gpd file to parse."""
    parse_gpd_file_mock = mocker.patch('smap_l2_gridder.grid.parse_gpd_file')

    get_target_grid_information(group, short_name)
    parse_gpd_file_mock.assert_called_with(expected)


def test_flatten_2d_data(mocker):
    """Test flattening flows."""
    dt = DataTree()
    dt['test_var'] = DataArray(np.random.randint(1, 101, size=(5, 3)))
    dt['test_other_var'] = DataArray(np.random.randint(1, 101, size=(5, 3)))

    split_spy = mocker.spy(grid, 'split_2d_variable')

    ### Test single variable flattened
    mocker.patch(
        'smap_l2_gridder.grid.get_flattened_variables', return_value={'test_var'}
    )
    _ = flatten_2d_data(dt, 'short_name')

    split_spy.assert_called_once_with(dt, 'test_var')

    ### Test multiple variables flattened
    mocker.resetall()
    mocker.patch(
        'smap_l2_gridder.grid.get_flattened_variables',
        return_value={'test_var', 'test_other_var'},
    )
    _ = flatten_2d_data(dt, 'short_name')
    split_spy.assert_has_calls(
        [call(dt, 'test_var'), call(dt, 'test_other_var')], any_order=True
    )

    ### Test no flattening
    mocker.resetall()
    mocker.patch('smap_l2_gridder.grid.get_flattened_variables', return_value=set())
    _ = flatten_2d_data(dt, 'short_name')
    split_spy.assert_not_called()


def test_split_2d_variable():
    """Test variable data splits correctly."""
    data = np.random.randint(0, 101, size=(6, 3))
    var = DataArray(data, dims=['phony_dim_0', 'phony_dim_1'])
    dt = DataTree()
    dt['test_var'] = var

    expected_1 = data[:, 0]
    expected_2 = data[:, 1]
    expected_3 = data[:, 2]

    result = split_2d_variable(dt, 'test_var')

    assert 'test_var_1' in result
    assert 'test_var_2' in result
    assert 'test_var_3' in result
    assert 'test_var' not in result

    np.testing.assert_array_equal(result['test_var_1'].data, expected_1)
    np.testing.assert_array_equal(result['test_var_2'].data, expected_2)
    np.testing.assert_array_equal(result['test_var_3'].data, expected_3)


@pytest.mark.parametrize('size', [(6, 4), (1, 7, 3)])
def test_split_2d_variable_invalid_shapes(size):
    """Test error cases when bad variable shapes passed."""
    dt = DataTree()
    dt['test_var'] = DataArray(np.random.randint(0, 101, size=size))

    with pytest.raises(InvalidVariableShape):
        split_2d_variable(dt, 'test_var')


@pytest.mark.parametrize(
    'dtype,expected',
    [
        (np.float32, True),
        (np.int64, True),
        (np.datetime64, True),
        (np.bool_, True),
        (np.complex128, True),
        (str, False),
        (np.dtype('U25'), False),
        (np.str_, False),
        (np.object_, False),
    ],
)
def test_is_compressible(dtype, expected):
    """Test the compressible types."""
    assert is_compressible(dtype) == expected


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
