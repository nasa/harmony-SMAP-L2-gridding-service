"""Set up common pytest fixtures."""

# ruff: noqa: E501

from datetime import datetime

import numpy as np
import pytest
from harmony_service_lib.util import bbox_to_geometry
from pystac import Asset, Catalog, Item
from xarray import DataArray, DataTree, open_datatree


# Fixtures
@pytest.fixture(name='sample_SPL2SMP_E_file')
def sample_SPL2SMP_E_file(tmp_path) -> str:
    """Create a sample DataTree file for testing.

    A sample DataTree is created with the approximate shape of a SPL2SMP_E file

    The test data is repeated for both global and polar groups.

    The tree is written to disk and the filename is returned.

    """
    dt = DataTree()
    dt['Metadata/Lineage/DEMSLP'] = DataTree()
    dt['Metadata/Lineage/DEMSLP'].attrs['Description'] = (
        'Representative surface slope data for each of the 9 km cells'
    )
    dt['Metadata/DatasetIdentification'] = DataArray(attrs={'shortName': 'SPL2SMP_E'})

    groups = ['Soil_Moisture_Retrieval_Data', 'Soil_Moisture_Retrieval_Data_Polar']
    for group in groups:
        dt[f'{group}'] = DataTree()
        dt[f'{group}/EASE_column_index'] = DataArray(
            data=np.array([1175, 1175, 1175, 1175, 1175], dtype=np.uint16),
            dims=['phony_dim_0'],
            name='EASE_column_index',
            attrs={
                'long_name': 'The column index of the 9 km EASE grid cell...',
                'valid_min': 0,
                'valid_max': 3855,
                '_FillValue': np.uint16(65534),
            },
        )

        dt[f'{group}/EASE_row_index'] = DataArray(
            data=np.array([1603, 1604, 1605, 1606, 1607], dtype=np.uint16),
            dims=['phony_dim_0'],
            attrs={
                'long_name': 'The row index of the 9 km EASE grid cell...',
                'valid_min': 0,
                'valid_max': 1623,
                '_FillValue': np.uint16(65534),
            },
        )

        dt[f'{group}/albedo'] = DataArray(
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

        # This part of the fixture REALLY slow when running tests.  Using it
        # adds 7 seconds(!!) to the run time. Really there is only one useful
        # test that needs this.  I tested this function outside of pytest and
        # it's not acting like a bottle neck so I'm not sure what to do. But
        # for now I'll remove this and use mark to skip the test.

        # dt[f'{group}/tb_time_utc'] = DataArray(
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
    return tmp_file


@pytest.fixture(name='sample_SPL2SMAP_file')
def sample_SPL2SMAP_file(tmp_path) -> str:
    """Create a sample DataTree file for testing.

    A sample DataTree is created with the approximate shape of a SPL2SMAP file

    The tree is written to disk and the filename is returned.

    """
    dt = DataTree()
    dt['Metadata/DatasetIdentification'] = DataArray(attrs={'shortName': 'SPL2SMAP'})

    dt['Soil_Moisture_Retrieval_Data'] = DataTree()
    dt['Soil_Moisture_Retrieval_Data/EASE_column_index'] = DataArray(
        data=np.array([1175, 1175, 1175, 1175, 1175], dtype=np.uint16),
        dims=['phony_dim_0'],
        attrs={
            'long_name': 'The column index of the 9 km EASE grid cell that contains the associated data.',
            'coordinates': '/Soil_Moisture_Retrieval_Data/latitude /Soil_Moisture_Retrieval_Data/longitude',
            'valid_min': 0,
            'valid_max': 65535,
            '_FillValue': np.uint16(65534),
        },
    )

    dt['Soil_Moisture_Retrieval_Data/EASE_row_index'] = DataArray(
        data=np.array([1603, 1604, 1605, 1606, 1607], dtype=np.uint16),
        dims=['phony_dim_0'],
        attrs={
            'long_name': 'The row index of the 9 km EASE grid cell that contains the associated data.',
            'coordinates': '/Soil_Moisture_Retrieval_Data/latitude /Soil_Moisture_Retrieval_Data/longitude',
            'valid_min': 0,
            'valid_max': 65535,
            '_FillValue': np.uint16(65534),
        },
    )

    dt['Soil_Moisture_Retrieval_Data/albedo'] = DataArray(
        data=np.array([0.0009434, 0.00136986, 0.0025, 0.0, -9999.0], dtype=np.float32),
        dims=['phony_dim_0'],
        attrs={
            'long_name': 'Diffuse reflecting power of the Earth&apos;s surface within the grid cell.',
            'coordinates': '/Soil_Moisture_Retrieval_Data/latitude /Soil_Moisture_Retrieval_Data/longitude',
            'valid_min': 0.0,
            'valid_max': 1.0,
            '_FillValue': np.float32(-9999.0),
        },
    )

    dt['Soil_Moisture_Retrieval_Data_3km'] = DataTree()
    dt['Soil_Moisture_Retrieval_Data_3km/EASE_column_index_3km'] = DataArray(
        data=np.array([1175, 1175, 1175, 1175, 1175], dtype=np.uint16),
        dims=['phony_dim_1'],
        attrs={
            'long_name': 'The column index of the 3 km EASE grid cell that contains the associated data.',
            'coordinates': '/Soil_Moisture_Retrieval_Data_3km/latitude_3km /Soil_Moisture_Retrieval_Data_3km/longitude_3km',
            'valid_min': 0,
            'valid_max': 65535,
            '_FillValue': np.uint16(65534),
        },
    )
    dt['Soil_Moisture_Retrieval_Data_3km/EASE_row_index_3km'] = DataArray(
        data=np.array([1603, 1604, 1605, 1606, 1607], dtype=np.uint16),
        dims=['phony_dim_1'],
        attrs={
            'long_name': 'The column index of the 3 km EASE grid cell that contains the associated data.',
            'coordinates': '/Soil_Moisture_Retrieval_Data_3km/latitude_3km /Soil_Moisture_Retrieval_Data_3km/longitude_3km',
            'valid_min': 0,
            'valid_max': 65535,
            '_FillValue': np.uint16(65534),
        },
    )

    dt['Soil_Moisture_Retrieval_Data_3km/albedo_3km'] = DataArray(
        data=np.array([0.0009434, 0.00136986, 0.0025, 0.0, -9999.0], dtype=np.float32),
        dims=['phony_dim_1'],
        attrs={
            'long_name': 'Diffuse reflecting power of the Earth&apos;s surface within the 3 km EASE grid cell.',
            'coordinates': '/Soil_Moisture_Retrieval_Data_3km/latitude_3km /Soil_Moisture_Retrieval_Data_3km/longitude_3km',
            'valid_min': 0.0,
            'valid_max': 1.0,
            '_FillValue': np.float32(-9999.0),
        },
    )

    # Round trip this to a file so that the encoding values are what we see
    # when we read from a NetCDF file.
    tmp_file = tmp_path / 'tmp_output.nc'
    dt.to_netcdf(tmp_file)
    return tmp_file


@pytest.fixture
def sample_datatree(request) -> DataTree:
    """A specified datatree fixture is generated, opened and returned.

    If no parameter is present on request, use the SPL2SMP_E fixture.
    """
    fixture_name = (
        request.param if hasattr(request, 'param') else 'sample_SPL2SMP_E_file'
    )
    datatree_file = request.getfixturevalue(fixture_name)
    dt2 = open_datatree(datatree_file, decode_times=False)
    return dt2


@pytest.fixture
def sample_stac() -> Catalog:
    """Creates a generic SpatioTemporal Asset Catalog (STAC).

    Used as a valid input for SMAPL2GridderAdapter initialization

    For simplicity the geometric and temporal properties of each item are
    set to default values.

    """
    catalog = Catalog(id='input catalog', description='test input')

    item = Item(
        id='input granule',
        bbox=[-180, -90, 180, 90],
        geometry=bbox_to_geometry([-180, -90, 180, 90]),
        datetime=datetime(2020, 1, 1),
        properties={'props': 'None'},
    )

    item.add_asset(
        'input data',
        Asset(
            'https://www.example.com/input.h5',
            media_type='application/x-hdf',
            roles=['data'],
        ),
    )
    catalog.add_item(item)

    return catalog
