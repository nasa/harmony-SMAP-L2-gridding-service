"""Collection information.

Define the data hierarchies necessary for gridding collections with the SMAP L2
Gridder.

While the input files are hierarchical, and in hdf format, they are not fully
self describing. Each griddable variable is connected to two variables that
contain the column and row of a grid, but there is not a fully standard
location for finding those locations.  Additionally, there are a number of
different resolution grids and coordinate reference systems, identified by a
gpd file and epsg code.

"""

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
            },
            'Soil_Moisture_Retrieval_Data_Polar': {
                'row': 'Soil_Moisture_Retrieval_Data_Polar/EASE_row_index',
                'col': 'Soil_Moisture_Retrieval_Data_Polar/EASE_column_index',
                **GRIDS['N09km'],
            },
        },
    },
    'SPL2SMAP': {
        'metadata': ['Metadata'],
        'data_groups': {
            'Soil_Moisture_Retrieval_Data': {**STANDARD_LOCATIONS, **GRIDS['M09km']},
            'Soil_Moisture_Retrieval_Data_3km': {
                'row': 'Soil_Moisture_Retrieval_Data_3km/EASE_row_index_3km',
                'col': 'Soil_Moisture_Retrieval_Data_3km/EASE_column_index_3km',
                **GRIDS['M03km'],
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
