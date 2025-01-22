"""Grid L2G data into encoded EASE Grid output.

L2G data represents a gridded swath in an EASE projected grid.  These are the
routines to translate the 1D intput arrays into the EASE grid output format
"""

from collections.abc import Iterable
from logging import Logger
from pathlib import Path

import numpy as np
from xarray import DataArray, DataTree, open_datatree

from .crs import EPSG_6931_WKT, EPSG_6933_WKT, compute_dims, create_crs, parse_gpd_file
from .exceptions import InvalidCollectionError


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
    short_name = get_dataset_shortname(in_data)

    out_data = transfer_metadata(in_data, out_data)

    # Process grids from all top level groups that are not only Metadata
    data_node_names = set(in_data['/'].children) - set(get_metadata_children(in_data))

    for node_name in data_node_names:
        grid_info = get_grid_information(in_data, node_name, short_name)
        vars_to_grid = get_target_variables(in_data, node_name)

        # Add coordinates and CRS metadata for this node_name
        x_dim, y_dim = compute_dims(grid_info['target'])
        out_data[f'{node_name}/crs'] = create_crs(grid_info['target'])
        out_data[f'{node_name}/x-dim'] = x_dim
        out_data[f'{node_name}/y-dim'] = y_dim

        for var_name in vars_to_grid:
            full_var_name = f'{node_name}/{var_name}'
            out_data[full_var_name] = prepare_variable(
                in_data[full_var_name], grid_info
            )

    # write the output data file.
    out_data.to_netcdf(output_file)


def prepare_variable(var: DataTree | DataArray, grid_info: dict) -> DataArray:
    """Grid and annotate intput variable."""
    grid_data = grid_variable(var, grid_info)
    grid_data.attrs = {**var.attrs, 'grid_mapping': 'crs'}
    encoding = {
        '_FillValue': variable_fill_value(var),
        'coordinates': var.encoding.get('coordinates', None),
        # can't zip strings
        **({'zlib': True, 'complevel': 6} if var.name != 'tb_time_utc' else {}),
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


def get_target_variables(in_data: DataTree, node: str) -> Iterable[str]:
    """Get variables to be regridded in the output file."""
    return in_data[node].data_vars


def get_grid_information(in_dt: DataTree, node: str, short_name: str) -> dict:
    """Get the column and row indices and target grid information.

    Using the node name and collection. Retrieve all of the information needed
    to grid the node's data.

    """
    src_grid_info = {}
    row, column = locate_row_and_column_in_node(in_dt, node, short_name)
    src_grid_info['rows'] = row.astype(row.encoding.get('dtype', 'uint16'))
    src_grid_info['cols'] = column.astype(column.encoding.get('dtype', 'uint16'))

    grid_info = {}
    grid_info['src'] = src_grid_info
    grid_info['target'] = get_target_grid_information(node, short_name)

    return grid_info


def locate_row_and_column_in_node(
    in_dt: DataTree, node: str, short_name: str
) -> tuple[DataArray, DataArray]:
    """Return the row and column information for this node.

    Use the short_name to determine the correct location of the row and column
    indices variables within in the input DataTree structure.

    """
    if short_name == 'SPL2SMP_E':
        return (in_dt[f'{node}/EASE_row_index'], in_dt[f'{node}/EASE_column_index'])
    elif short_name == 'SPL2SMAP':
        return (
            in_dt[spl2smap_index_locator(node, 'EASE_row_index')],
            in_dt[spl2smap_index_locator(node, 'EASE_column_index')],
        )
    else:
        raise InvalidCollectionError(f'Invalid collection: {short_name}.')


def spl2smap_index_locator(node: str, stem: str) -> str:
    """Returns path to the column or row index variable."""
    ext = '_3km' if node.endswith('_3km') else ''
    return f'{node}/{stem}{ext}'


def get_column_dataarray(in_dt: DataTree, node: str, short_name: str) -> DataArray:
    """Return the dataarray containing the node's column indices."""
    return in_dt[f'/{node}/EASE_column_index']


def get_target_grid_information(node: str, short_name: str) -> dict:
    """Return the target grid informaton.

    Using the node name and collection short name return in the correct gpd and
    epsg information for the target grid.

    """
    gpd_name, wkt = get_grid_and_crs(node, short_name)

    target_grid_info = parse_gpd_file(gpd_name)
    target_grid_info['wkt'] = wkt
    return target_grid_info


def get_grid_and_crs(node, short_name):
    """Retrieve the grid and crs from collecton and node name."""
    if is_polar_node(node):
        gpd_name = 'EASE2_N09km.gpd'
        wkt = EPSG_6931_WKT
    else:
        gpd_name = 'EASE2_M09km.gpd'
        wkt = EPSG_6933_WKT

    return gpd_name, wkt


def is_polar_node(node: str) -> bool:
    """If the node name ends with "_Polar" it's the Northern Hemisphere data."""
    return node.endswith('_Polar')


def get_metadata_children(in_data: DataTree) -> list[str]:
    """Fetch nodes with metadata.

    List of top level datatree children containing metadata to transfer
    directly to output file.

    Note: This returns a constant for now, but may require reading the in_data
    in the future.
    """
    return ['Metadata']


def get_dataset_shortname(in_data: DataTree) -> str:
    """Extract the short name identifier from the dataset metadata."""
    return in_data['Metadata/DatasetIdentification'].shortName


def transfer_metadata(in_data: DataTree, out_data: DataTree) -> DataTree:
    """Transfer all metadata groups from input to the output datatree."""
    updated_data = out_data.copy()
    for group_name in get_metadata_children(in_data):
        updated_data[group_name] = in_data[group_name]

    return updated_data
