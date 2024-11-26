"""Set up common pytest fixtures."""

from datetime import datetime

import numpy as np
import pytest
from harmony_service_lib.util import bbox_to_geometry
from pystac import Asset, Catalog, Item
from xarray import DataArray, DataTree, open_datatree


# Fixtures
@pytest.fixture
def sample_datatree_file(tmp_path) -> str:
    """Create a sample DataTree file for testing.

    The test data is repeated for both global and polar nodes.

    A sample DataTree is created and written to disk.

    The filename is returned.
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

        # This part of the fixture REALLY slow. Including it adds 7 seconds(!!)
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
    return tmp_file


@pytest.fixture
def sample_datatree(sample_datatree_file) -> DataTree:
    """A sample datatree is gennerated and returned after being read from disk.

    This represents the expected shape of an SPL2SMP_E granule.
    """
    dt2 = open_datatree(sample_datatree_file, decode_times=False)
    return dt2


@pytest.fixture
def stack_catalog() -> Catalog:
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
        properties=None,
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
