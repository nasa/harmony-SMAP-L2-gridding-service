"""Grid L2G data into encoded EASE Grid output.

L2G data represents a gridded swath in an EASE projected grid.  These are the
routines to translate the 1D intput arrays into the EASE grid output format
"""

from collections.abc import Iterable
from logging import Logger
from pathlib import Path

import numpy as np
from pyproj import CRS
from xarray import DataArray, DataTree, open_datatree

from .collections import (
    get_collection_group_info,
    get_collection_info,
    get_dropped_variables,
)
from .crs import compute_dims, create_crs, parse_gpd_file


def transform_l2g_input(
    input_filename: Path, output_filename: Path, logger: Logger
) -> None:
    """Entrypoint for L2G-Gridding-Service.

    Opens input and processes the data to a new output file.
    """
    with open_datatree(input_filename, decode_times=False) as in_data:
        process_input(in_data, output_filename, logger=logger)


def process_input(in_data: DataTree, output_file: Path, logger: None | Logger = None):
    """Process input file to generate gridded output file."""
    out_data = DataTree()

    short_name = get_collection_shortname(in_data)

    out_data = transfer_metadata(in_data, out_data)

    # Process grids from all top level groups that are not only Metadata
    data_group_names = get_data_groups(in_data)

    for group_name in data_group_names:
        grid_info = get_grid_information(in_data, group_name, short_name)
        vars_to_grid = get_target_variables(in_data, group_name, short_name)

        # Add coordinates and CRS metadata for this group_name
        x_dim, y_dim = compute_dims(grid_info['target'])
        out_data[f'{group_name}/crs'] = create_crs(grid_info['target'])
        out_data[f'{group_name}/x-dim'] = x_dim
        out_data[f'{group_name}/y-dim'] = y_dim

        for var_name in vars_to_grid:
            full_var_name = f'{group_name}/{var_name}'
            out_data[full_var_name] = prepare_variable(
                in_data[full_var_name], grid_info
            )

    # write the output data file.
    out_data.to_netcdf(output_file)


def prepare_variable(var: DataTree | DataArray, grid_info: dict) -> DataArray:
    """Grid and annotate intput variable."""
    grid_data = grid_variable(var, grid_info)
    grid_data.attrs = {**var.attrs, 'grid_mapping': 'crs'}
    unzippable = ['tb_time_utc']  # can't zip strings
    encoding = {
        '_FillValue': variable_fill_value(var),
        'coordinates': var.encoding.get('coordinates', None),
        **({'zlib': True, 'complevel': 6} if var.name not in unzippable else {}),
    }
    grid_data.encoding.update(encoding)
    return grid_data


def grid_variable(var: DataTree | DataArray, grid_info: dict) -> DataArray:
    """Regrid the input 1D variable into a 2D grid using the grid_info."""
    fill_val = variable_fill_value(var)
    grid = np.full(
        (grid_info['target']['Grid Height'], grid_info['target']['Grid Width']),
        fill_val,
        dtype=(var.encoding.get('dtype', var.dtype)),
    )
    try:
        valid_mask = ~np.isnan(var.data)
    except TypeError:
        # tb_time_utc is type string
        valid_mask = var.data != ''
    valid_rows = grid_info['src']['rows'].data[valid_mask]
    valid_cols = grid_info['src']['cols'].data[valid_mask]
    valid_values = var.data[valid_mask]
    grid[valid_rows, valid_cols] = valid_values
    return DataArray(grid, dims=['y-dim', 'x-dim'])


def variable_fill_value(var: DataTree | DataArray) -> np.integer | np.floating | None:
    """Determine the correct fill value for the input variable.

    a fill value is found by searching in order:
      - encoding._FillValue
      - attrs._FillValue
      - missing_value

    If not found, a default_fill_value is determined base on the input
    varaiable datatype.
    """
    fill_value = var.encoding.get('_FillValue')
    if fill_value is None:
        fill_value = var.attrs.get('_FillValue')
    if fill_value is None:
        fill_value = var.attrs.get('missing_value')
    if fill_value is None:
        fill_value = default_fill_value(var.encoding.get('dtype', var.dtype))
    return fill_value


def default_fill_value(data_type: np.dtype | None) -> np.integer | np.floating | None:
    """Return an appropriate fill value for the input data type.

    These values were pulled from the on-prem system's
    get_special_fill_value routine.

    it returns:
      - None if type isn't numeric
      - -9999.0 if type is floating
      - Max value if type is an integer.
    """
    if not np.issubdtype(data_type, np.number):
        return None

    if np.issubdtype(data_type, np.floating):
        return np.dtype(data_type).type(-9999.0)

    # np.issubdtype(data_type, np.integer):
    return np.dtype(data_type).type(np.iinfo(data_type).max)


def get_target_variables(
    in_data: DataTree, group: str, short_name: str
) -> Iterable[str]:
    """Get variables to be regridded in the output file."""
    dropped_variables = get_dropped_variables(short_name, group)
    return set(in_data[group].data_vars) - set(dropped_variables)


def get_grid_information(in_dt: DataTree, group: str, short_name: str) -> dict:
    """Gets required information to perform the gridding operation.

    Using the group name and collection's short_name, find and returns the
    column and row indices variables as well as the output target grid
    information.

    """
    grid_info = {}
    grid_info['src'] = locate_row_and_column_for_group(in_dt, group, short_name)
    grid_info['target'] = get_target_grid_information(group, short_name)

    return grid_info


def locate_row_and_column_for_group(
    in_dt: DataTree, group: str, short_name: str
) -> dict[str, DataArray]:
    """Return the row and column information for this group.

    Use the short_name to determine the correct location of the row and column
    indices variables within in the input DataTree structure.

    """
    info = get_collection_group_info(short_name, group)
    row = in_dt[info['row']]
    column = in_dt[info['col']]
    return {
        'rows': row.astype(row.encoding.get('dtype', 'uint16')),
        'cols': column.astype(column.encoding.get('dtype', 'uint16')),
    }


def get_target_grid_information(group: str, short_name: str) -> dict:
    """Return the target grid informaton.

    Using the group name and collection short name look up the gpd and epsg
    code that represent the target grid.

    """
    info = get_collection_group_info(short_name, group)
    target_grid_info = parse_gpd_file(info['gpd'])
    target_grid_info['wkt'] = CRS(info['epsg']).to_wkt()
    return target_grid_info


def get_data_groups(in_data: DataTree) -> set[str]:
    """Returns list of input groups containing griddable data."""
    return set(in_data['/'].children) - set(get_metadata_children(in_data))


def get_metadata_children(in_data: DataTree) -> list[str]:
    """Fetch list of groups containing only metadata.

    List of top level datatree children containing only metadata to transfer
    directly to output file without any changes.

    """
    collection_config = get_collection_info(get_collection_shortname(in_data))
    return collection_config['metadata']


def get_collection_shortname(in_data: DataTree) -> str:
    """Extract the short name identifier from the dataset metadata."""
    return in_data['Metadata/DatasetIdentification'].shortName


def transfer_metadata(in_data: DataTree, out_data: DataTree) -> DataTree:
    """Transfer all metadata groups from input to the output datatree."""
    updated_data = out_data.copy()
    for group_name in get_metadata_children(in_data):
        updated_data[group_name] = in_data[group_name]

    return updated_data
