"""Collection information.

Defines hierarchies necessary for gridding collections with the SMAP L2 Gridder.

While the input files are hierarchical and in hdf format, they are not fully
self describing. Each griddable variable is tied to two variables that contain
the column and row of a grid into which the value should be placed. But these
column and row indices are not always in the same location.  Additionally,
there are a number of different resolution grids and coordinate reference
systems, that here are identified by a gpd file and epsg code that are
described in the documentation for the dataset but are hard/impossible to
determine by looking at the files themselves, for this reason we explictly lay
out this information in this file along with helper routines to ease access.

"""

from .exceptions import InvalidCollectionError

STANDARD_LOCATIONS = {
    'row': 'Soil_Moisture_Retrieval_Data/EASE_row_index',
    'col': 'Soil_Moisture_Retrieval_Data/EASE_column_index',
}

GRIDS = {
    'M03km': {'gpd': 'EASE2_M03km.gpd', 'epsg': 'EPSG:6933'},
    'M09km': {'gpd': 'EASE2_M09km.gpd', 'epsg': 'EPSG:6933'},
    'M36km': {'gpd': 'EASE2_M36km.gpd', 'epsg': 'EPSG:6933'},
    'N09km': {'gpd': 'EASE2_N09km.gpd', 'epsg': 'EPSG:6931'},
}


COLLECTION_INFORMATION = {
    'SPL2SMP_E': {
        'metadata': ['Metadata'],
        'data_groups': {
            'Soil_Moisture_Retrieval_Data': {
                **STANDARD_LOCATIONS,
                **GRIDS['M09km'],
                'dropped_variables': ['tb_time_utc'],
            },
            'Soil_Moisture_Retrieval_Data_Polar': {
                'row': 'Soil_Moisture_Retrieval_Data_Polar/EASE_row_index',
                'col': 'Soil_Moisture_Retrieval_Data_Polar/EASE_column_index',
                **GRIDS['N09km'],
                'dropped_variables': ['tb_time_utc'],
            },
        },
    },
    'SPL2SMAP': {
        'metadata': ['Metadata'],
        'data_groups': {
            'Soil_Moisture_Retrieval_Data': {
                **STANDARD_LOCATIONS,
                **GRIDS['M09km'],
                'dropped_variables': ['spacecraft_overpass_time_utc'],
            },
            'Soil_Moisture_Retrieval_Data_3km': {
                'row': 'Soil_Moisture_Retrieval_Data_3km/EASE_row_index_3km',
                'col': 'Soil_Moisture_Retrieval_Data_3km/EASE_column_index_3km',
                **GRIDS['M03km'],
                'dropped_variables': ['spacecraft_overpass_time_utc'],
            },
        },
    },
    'SPL2SMA': {
        'metadata': ['Metadata'],
        'data_groups': {
            'Ancillary_Data': {**STANDARD_LOCATIONS, **GRIDS['M03km']},
            'Radar_Data': {**STANDARD_LOCATIONS, **GRIDS['M03km']},
            'Soil_Moisture_Retrieval_Data': {**STANDARD_LOCATIONS, **GRIDS['M03km']},
        },
    },
    'SPL2SMP': {
        'metadata': ['Metadata'],
        'data_groups': {
            'Soil_Moisture_Retrieval_Data': {
                **STANDARD_LOCATIONS,
                **GRIDS['M36km'],
            }
        },
    },
}


def get_all_information() -> dict:
    """Returns all known collection information.

    Mostly exists to mock tests.
    """
    return COLLECTION_INFORMATION


def get_collection_info(short_name: str) -> dict:
    """Return the configuration information for the short_name's collection."""
    try:
        return get_all_information()[short_name]
    except KeyError as exc:
        raise InvalidCollectionError(
            f'No collection information for {short_name}'
        ) from exc


def get_collection_group_info(short_name: str, group: str) -> dict:
    """Get basic information for a collection's group.

    Helper function to identify which information was incorrect when attempting
    to retrieve the desired gridding information

    """
    collection = get_collection_info(short_name)
    try:
        group_info = collection['data_groups'][group]
    except KeyError as exc:
        raise InvalidCollectionError(f'No group named {group} in {short_name}') from exc

    return group_info


def get_dropped_variables(short_name: str, group: str) -> set[str]:
    """Return a set of variables to be excluded from the processed file."""
    try:
        info = get_collection_group_info(short_name, group)
        dropped_vars = info['dropped_variables']
        return set(dropped_vars)
    except KeyError:
        return set()
