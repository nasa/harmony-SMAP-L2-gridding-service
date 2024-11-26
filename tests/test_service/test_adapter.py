"""End-to-end tests of the SMAP-L2-Gridding-Service."""

import pytest
from harmony_service_lib.message import Message as HarmonyMessage
from harmony_service_lib.util import config
from xarray import open_datatree

from harmony_service.adapter import SMAPL2GridderAdapter
from smap_l2_gridder.exceptions import InvalidGPDError


def test_process_sample_file(tmp_path, sample_datatree_file, stack_catalog, mocker):
    """Run a sample file through the adapter."""
    # override the adapter's working dir
    temp_dir_mock = mocker.patch('harmony_service.adapter.TemporaryDirectory')
    temp_dir_mock.return_value.__enter__.return_value = tmp_path

    # use a datatree fixture as the downloaded file
    download_mock = mocker.patch('harmony_service.adapter.download')
    download_mock.return_value = sample_datatree_file

    # set the output filename
    filename_mock = mocker.patch('harmony_service.adapter.generate_output_filename')
    output_filename = tmp_path / 'test-gridded.nc'
    filename_mock.return_value = output_filename

    stage_mock = mocker.patch('harmony_service.adapter.stage')
    staging_dir = tmp_path / 'staging'

    message = HarmonyMessage(
        {
            'accessToken': 'fake_token',
            'callback': 'https://example.com/',
            'sources': [{'collection': 'C1234-EEDTEST', 'shortName': 'smap_test'}],
            'stagingLocation': staging_dir,
            'user': 'fakeUsername',
            'format': {'mime': 'application/x-netcdf4'},
        }
    )

    # Set up Adapter class
    smap_l2_gridding_service = SMAPL2GridderAdapter(
        message, config=config(validate=False), catalog=stack_catalog
    )

    # Invoke the adapter.
    _, _ = smap_l2_gridding_service.invoke()

    asset_href = stack_catalog.get_item('input granule').assets['input data'].href

    download_mock.assert_called_once_with(
        asset_href,
        tmp_path,
        logger=mocker.ANY,
        cfg=mocker.ANY,
        access_token=message.accessToken,
    )

    stage_mock.assert_called_once_with(
        tmp_path / 'working_gridded.nc',
        output_filename,
        'application/x-netcdf4',
        location=message.stagingLocation,
        logger=mocker.ANY,
        cfg=mocker.ANY,
    )

    # Validate the gridded output data
    results = open_datatree(tmp_path / 'working_gridded.nc')
    assert set(results.groups) == set(
        (
            '/',
            '/Metadata',
            '/Soil_Moisture_Retrieval_Data',
            '/Soil_Moisture_Retrieval_Data_Polar',
            '/Metadata/Lineage',
            '/Metadata/Lineage/DEMSLP',
        )
    )
    assert results['Soil_Moisture_Retrieval_Data'].coords['x-dim'].name == 'x-dim'
    assert len(results['Soil_Moisture_Retrieval_Data'].coords['x-dim']) == 3856
    assert (
        results['Soil_Moisture_Retrieval_Data'].crs.attrs['projected_crs_name']
        == 'WGS 84 / NSIDC EASE-Grid 2.0 Global'
    )
    assert (
        results['Soil_Moisture_Retrieval_Data_Polar'].crs.attrs['projected_crs_name']
        == 'WGS 84 / NSIDC EASE-Grid 2.0 North'
    )
    assert set(results['Soil_Moisture_Retrieval_Data_Polar'].variables) == set(
        [
            'EASE_column_index',
            'EASE_row_index',
            'albedo',
            'crs',
            #'tb_time_utc',
            'x-dim',
            'y-dim',
        ]
    )
    assert set(results['Soil_Moisture_Retrieval_Data'].variables) == set(
        [
            'EASE_column_index',
            'EASE_row_index',
            'albedo',
            'crs',
            #'tb_time_utc',
            'x-dim',
            'y-dim',
        ]
    )


def test_process_sample_file_failure(
    tmp_path, stack_catalog, sample_datatree_file, mocker
):
    """Test failure."""
    # use a datatree fixture as the downloaded file
    download_mock = mocker.patch('harmony_service.adapter.download')
    download_mock.return_value = sample_datatree_file
    mocker.patch('harmony_service.adapter.generate_output_filename')
    mocker.patch('harmony_service.adapter.stage')

    get_grid_info_mock = mocker.patch('smap_l2_gridder.grid.get_grid_information')
    get_grid_info_mock.side_effect = InvalidGPDError('invalid gpd')

    message = HarmonyMessage(
        {
            'sources': [{'collection': 'C1234-EEDTEST'}],
        }
    )

    # Set up Adapter class
    smap_l2_gridding_service = SMAPL2GridderAdapter(
        message, config=config(validate=False), catalog=stack_catalog
    )

    # Invoke the adapter.
    with pytest.raises(InvalidGPDError) as error_info:
        smap_l2_gridding_service.invoke()

    assert 'invalid gpd' in str(error_info.value)
