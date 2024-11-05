"""Grid L2G data into encoded EASE Grid output.

L2G data represents a gridded swath in an EASE projected grid.  These are the
routines to translate the 1D intput arrays into the EASE grid output format
"""

from xarray import DataTree, DataArray
from numpy import ndarray, dtype
import numpy as np


def process_input(in_data: DataTree, output_file: str):
    decode_grid(in_data, output_file)


def decode_grid(in_data: DataTree, output_file: str):
    """Process input file to generate gridded output file."""
    out_data = DataTree()

    # First stab. We know what to do with these files in PoC.

    # copy over all the input metadata directly to the output file.
    out_data = transfer_metadata(in_data, out_data)

    data_node_names = set(in_data['/'].children) - set(get_metadata_children(in_data))

    # To regrid the variables: I will need to know the name of the child node,
    # it's column index full location, it's row index full location, the target
    # grid shape.
    for node_name in data_node_names:
        grid_info = get_target_grid_information(in_data, node_name)
        vars_to_grid = get_target_variables(in_data, node_name)
        for var_name in vars_to_grid:
            gridded_var_data = grid_variable(in_data[node_name][var_name], grid_info)
            # add variable to output data
            out_data[f'{node_name}/{var_name}'] = DataArray(
                gridded_var_data, dims=['y-dim', 'x-dim']
            )
            out_data[f'{node_name}/{var_name}'].attrs = in_data[node_name][
                var_name
            ].attrs
            out_data[f'{node_name}/{var_name}'].encoding.update(
                {'_FillValue': variable_fill_value(in_data[node_name][var_name])}
            )
            out_data[f'{node_name}/{var_name}'].encoding.update(
                {
                    'coordinates': in_data[node_name][var_name].encoding.get(
                        'coordinates', None
                    )
                }
            )

    # write the output data file.
    out_data.to_netcdf(output_file)


def grid_variable(var: DataTree | DataArray, grid_info: dict) -> DataArray:
    """Regrid the input 1D variable into a 2D grid using the grid_info."""
    fill_val = variable_fill_value(var)
    print(f'{var.name} fill: {fill_val}: {type(fill_val)}')
    grid = np.full(
        (grid_info['n_rows'], grid_info['n_cols']),
        fill_val,
        dtype=var.encoding['dtype'],
    )
    valid_mask = ~np.isnan(var.data)
    valid_rows = grid_info['rows'].data[valid_mask]
    valid_cols = grid_info['cols'].data[valid_mask]
    valid_values = var.data[valid_mask]
    grid[valid_rows, valid_cols] = valid_values
    # TODO [MHS, 11/07/2024]  Add dimension names x-dim, y-dim?
    return DataArray(grid)


def variable_fill_value(var: DataTree | DataArray) -> np.integer | np.floating | None:
    """Determine the correct fill value for the input variable.

    TODO [MHS, 11/07/2024] I'm not 100% sure how to simplify this if the fill values could be 0.
    """
    fill_value = var.encoding.get('_FillValue')
    if fill_value is None:
        fill_value = var.attrs.get('_FillValue')
    if fill_value is None:
        fill_value = var.attrs.get('missing_value')
    if fill_value is None:
        fill_value = default_fill_value(var.encoding.get('dtype'))
    return fill_value


def default_fill_value(data_type: np.dtype | None) -> np.integer | np.floating | None:
    """Return an appropriate fill value for the input data type.

    # TODO [MHS, 11/07/2024] I am going with the code from get_special_fill_value type
    from before. but I'm not sure if it's a good idea.

    """
    if not np.issubdtype(data_type, np.number):
        return None
    if np.issubdtype(data_type, np.floating):
        return np.dtype(data_type).type(-9999.0)
    if np.issubdtype(data_type, np.integer):
        return np.dtype(data_type).type(np.iinfo(data_type).max)
    return None


def get_target_variables(in_data: DataTree, node: str) -> list[str]:
    """get variables to be regridded in the output file.

    TODO [MHS, 11/07/2024]: This might be all variables, but also might have
    some special handling cases in the future. In this PoC it's just these.

    """
    return ['albedo', 'latitude', 'longitude', 'EASE_column_index', 'EASE_row_index']


def get_target_grid_information(in_data: DataTree, node: str) -> dict:
    """Get the column, row index locations and grid information for this node.

    For the PoC this will always be "node/EASE_column_index",
    "node/EASE_row_index", and EASE Grid 9km data either global or north grid.

    TODO [MHS, 11/06/2024] This goes in a different file later with logic to
    suss which grid each node is representing.

    """
    grid_info = {}
    row = in_data[f'/{node}/EASE_row_index']
    column = in_data[f'/{node}/EASE_column_index']
    grid_info['rows'] = row.astype(row.encoding.get('dtype', 'uint16'))
    grid_info['cols'] = column.astype(column.encoding.get('dtype', 'uint16'))

    if is_polar_node(node):
        grid_info['n_cols'] = 2000
        grid_info['n_rows'] = 2000
    else:
        grid_info['n_cols'] = 3856
        grid_info['n_rows'] = 1624

    return grid_info


def is_polar_node(node: str) -> bool:
    """If the node name ends with "_Polar" it's the Northern Hemisphere data."""
    return node.endswith('_Polar')


def get_metadata_children(in_data: DataTree) -> list[str]:
    """Fetch nodes with metadata.

    List of top level datatree children containing metadata to transfer
    directly to output file.

    """
    return ['Metadata']


def transfer_metadata(in_data: DataTree, out_data: DataTree) -> DataTree:
    """Transfer all metadata groups from input to the output datatree."""
    updated_data = out_data.copy()
    for group_name in get_metadata_children(in_data):
        updated_data[group_name] = in_data[group_name]

    return updated_data
