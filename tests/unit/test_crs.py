"""Unit test module for crs functionality."""

from pathlib import Path
from textwrap import dedent

import numpy as np
import pytest
from xarray import DataArray

from smap_l2_gridder.crs import (
    EPSG_6933_WKT,
    Geotransform,
    compute_dims,
    convert_value,
    create_crs,
    geotransform_from_target_info,
    parse_gpd_file,
    validate_gpd_style,
)
from smap_l2_gridder.exceptions import InvalidGPDError

EASE2_M09km_gpd_filename = (
    Path(__file__).parent.parent.parent / 'smap_l2_gridder/reference/EASE2_M09km.gpd'
)

# Sample data for testing
sample_target_info = {
    'Map Origin X': -5000.0,
    'Map Origin Y': -5000.0,
    'Grid Map Units per Cell': 1000.0,
    'Grid Width': 10,
    'Grid Height': 10,
    'Grid Map Origin Column': -0.5,
    'Grid Map Origin Row': -0.5,
    'wkt': EPSG_6933_WKT,
}


def test_geotransform():
    """Test basic geotransformation computations."""
    gt = Geotransform(-2000.0, 1000.0, 0.0, 0.0, 0.0, -1000.0)
    x, y = gt.col_row_to_xy(0, 0)
    assert np.isclose(x, -1500.0)
    assert np.isclose(y, -500.0)
    x2, y2 = gt.col_row_to_xy(1, 1)
    assert np.isclose(x2, -500.0)
    assert np.isclose(y2, -1500.0)


def test_geotransform_from_target_info():
    """Tests target info will be parsed for a geotransform."""
    gt = geotransform_from_target_info(sample_target_info)
    assert isinstance(gt, Geotransform)
    assert np.isclose(gt.top_left_x, -5000.0)
    assert np.isclose(gt.top_left_y, -5000.0)
    assert np.isclose(gt.row_rotation, 0.0)
    assert np.isclose(gt.column_rotation, 0.0)
    assert np.isclose(gt.pixel_width, 1000.0)
    assert np.isclose(gt.pixel_height, -1000.0)


def test_validate_gpd_style_valid():
    """Valid target information will validate."""
    validate_gpd_style(sample_target_info)


def test_validate_gpd_style_invalid():
    """Tests that only the expected gpd format will convert to geotransform."""
    invalid_target_info = sample_target_info.copy()
    invalid_target_info['Grid Map Origin Column'] = 0.0
    with pytest.raises(InvalidGPDError):
        validate_gpd_style(invalid_target_info)


def test_convert_value():
    """Ensure gpd parsed values are converted to correct data types."""
    assert convert_value(' 123 ') == 123
    assert convert_value(' 123.45 ') == np.float64(123.45)
    assert convert_value('abc ') == 'abc'


def test_parse_gpd_file(tmp_path):
    """Test GPD files are correctly parsed."""
    gpd_content = dedent(
        """
    ; Example gpd for parsing
    Map Origin X: -7000.0  ; pinned location for Map Origin X
    Map Origin Y: 0.0
    Grid Map Units per Cell: 1000.0
    Grid Map Origin Column: -0.5
    Grid Map Origin Row: -0.5
    Something That Exists But Is Not Used: Has A Value
    """
    ).strip()

    gpd_file = tmp_path / 'test.gpd'
    gpd_file.write_text(gpd_content)

    result = parse_gpd_file(str(gpd_file))
    assert result['Map Origin X'] == -7000.0
    assert result['Map Origin Y'] == 0.0
    assert result['Grid Map Units per Cell'] == 1000.0
    assert result['Something That Exists But Is Not Used'] == 'Has A Value'


def test_create_crs():
    """Test create crs transforms input info into array with metadata."""
    crs_data_array = create_crs(sample_target_info)
    assert 'crs_wkt' in crs_data_array.attrs
    assert 'NSIDC EASE-Grid 2.0 Global' in crs_data_array.crs_wkt, (
        f'expected "NSIDC EASE-Grid 2.0 Global" in {crs_data_array.crs_wkt}'
    )
    assert crs_data_array.attrs['proj'] == (
        '+proj=cea +lat_ts=30 +lon_0=0 +x_0=0 '
        '+y_0=0 +datum=WGS84 +units=m +no_defs +type=crs'
    )
    assert isinstance(crs_data_array, DataArray)


def test_compute_dims():
    """Test compute dims against a known entity.

    Use the EASE2 Global 9km grid. and verify a few values against known values
    pulled form NSIDC-0772 dataset

    """
    EASE2_M09km_grid_info = parse_gpd_file(EASE2_M09km_gpd_filename)
    x_dim, y_dim = compute_dims(EASE2_M09km_grid_info)
    assert len(x_dim) == EASE2_M09km_grid_info['Grid Width']
    assert len(y_dim) == EASE2_M09km_grid_info['Grid Height']
    selected_y_index = np.array([0, 203, 406, 609, 812, 1014, 1217, 1420, 1623])
    selected_x_index = np.array([0, 482, 964, 1446, 1928, 2409, 2891, 3373, 3855])
    expected_x_values = np.array(
        [
            -1.7363026417556427e07,
            -1.3021143806266051e07,
            -8.6792611949756760e06,
            -4.3373785836853012e06,
            4.5040276050753891e03,
            4.3373785836853050e06,
            8.6792611949756779e06,
            1.3021143806266055e07,
            1.7363026417556427e07,
        ],
        dtype=np.float64,
    )
    expected_y_values = np.array(
        [
            7.3100368030335270e06,
            5.4814015953738764e06,
            3.6527663877142267e06,
            1.8241311800545761e06,
            -4.5040276050735265e03,
            -1.8241311800545771e06,
            -3.6527663877142277e06,
            -5.4814015953738783e06,
            -7.3100368030335270e06,
        ],
        dtype=np.float64,
    )

    np.testing.assert_array_almost_equal(x_dim[selected_x_index], expected_x_values)
    np.testing.assert_array_almost_equal(y_dim[selected_y_index], expected_y_values)
