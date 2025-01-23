"""Info particular to geolocating the input data to a target grid."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import xarray as xr
from pyproj.crs import CRS
from xarray import DataArray

from smap_l2_gridder.exceptions import InvalidGPDError


@dataclass
class Geotransform:
    """Class for holding a GDAL-style 6-element geotransform."""

    top_left_x: np.float64
    pixel_width: np.float64
    row_rotation: np.float64
    top_left_y: np.float64
    column_rotation: np.float64
    pixel_height: np.float64

    def col_row_to_xy(self, col: int, row: int) -> tuple[np.float64, np.float64]:
        """Convert grid cell location to x,y coordinate."""
        # Geotransform is defined from upper left corner as (0,0), so adjust
        # input value to the center of grid at (.5, .5)
        adj_col = col + 0.5
        adj_row = row + 0.5

        x = self.top_left_x + adj_col * self.pixel_width + adj_row * self.row_rotation
        y = (
            self.top_left_y
            + adj_col * self.column_rotation
            + adj_row * self.pixel_height
        )
        return x, y


def geotransform_from_target_info(target_info: dict) -> Geotransform:
    """Return a geotransform from the grid_info dict.

    grid_info contains a parsed NSIDC gpd file.

    GT(0) x-coordinate of the upper-left corner of the upper-left pixel.
    GT(1) w-e pixel resolution / pixel width.
    GT(2) row rotation (typically zero).
    GT(3) y-coordinate of the upper-left corner of the upper-left pixel.
    GT(4) column rotation (typically zero).
    GT(5) n-s pixel resolution / pixel height (negative value for a north-up image).

    """
    validate_gpd_style(target_info)
    return Geotransform(
        target_info['Map Origin X'],
        target_info['Grid Map Units per Cell'],
        np.float64(0.0),
        target_info['Map Origin Y'],
        np.float64(0.0),
        -1.0 * target_info['Grid Map Units per Cell'],
    )


def validate_gpd_style(target_info: dict) -> None:
    """Raise error if the gpd is non-standard."""
    if (target_info['Grid Map Origin Column'] != -0.5) or (
        target_info['Grid Map Origin Row'] != -0.5
    ):
        raise InvalidGPDError('Can not use non standard gpd.')


def convert_value(value: str) -> str | np.float64 | np.long:
    """Convert gpd value to appropriate type."""
    value = value.strip()
    try:
        if '.' in value:
            return np.float64(value)
        return np.long(value)
    except ValueError:
        return value


def parse_gpd_file(gpd_name: str) -> dict:
    """Parse a grid parameter definition file and return a dictionary of parameters.

    Parameters:
    -----------
    filename : str
        Full path to a grid parameter definition file
       or
        Name of a gpd file in the references directory.

    Returns:
    --------
    dict
        Dictionary containing parameter names as keys and their values as values.
        Decimal numbers are converted to np.float64
        Integer-like numbers are converted to np.long
        Non-numeric values remain as strings

    """
    gpd_info = {}

    if Path(gpd_name).exists():
        filename = gpd_name
    else:
        filename = f'{Path(__file__).parent}/reference/{gpd_name}'

    with open(filename, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(';'):
                continue

            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                # Remove comments and strip whitespace
                value = value.split(';')[0].strip()

                if key and value:
                    gpd_info[key] = convert_value(value)

    return gpd_info


def create_crs(target_info: dict) -> DataArray:
    """Return the correct CRS for the target grid."""
    crs = CRS(target_info['wkt'])
    the_crs = xr.DataArray(data=b'', attrs={**crs.to_cf(), 'proj': crs.to_proj4()})
    return the_crs


def compute_dims(target_info: dict) -> tuple[DataArray, DataArray]:
    """Compute the coordinate dimension.

    Parameters:
    ----------
    target_info : dict
       target grid information dictionary.

    """
    n_cols = target_info['Grid Width']
    n_rows = target_info['Grid Height']
    geotransform = geotransform_from_target_info(target_info)

    # compute the x,y locations along a column and row
    column_dimensions = [geotransform.col_row_to_xy(i, 0) for i in range(n_cols)]
    row_dimensions = [geotransform.col_row_to_xy(0, i) for i in range(n_rows)]
    # pull out dimension values
    x_values = np.array([x for x, y in column_dimensions], dtype=np.float64)
    y_values = np.array([y for x, y in row_dimensions], dtype=np.float64)

    x_dim = xr.DataArray(
        data=x_values,
        dims=['x-dim'],
        coords={'x-dim': x_values},
        attrs={
            'standard_name': 'projection_x_coordinate',
            'long_name': 'x coordinate of projection',
            'units': 'm',
        },
    )
    y_dim = xr.DataArray(
        data=y_values,
        dims=['y-dim'],
        coords=({'y-dim': y_values}),
        attrs={
            'standard_name': 'projection_y_coordinate',
            'long_name': 'y coordinate of projection',
            'units': 'm',
        },
    )
    x_dim.encoding = {'_FillValue': None}
    y_dim.encoding = {'_FillValue': None}
    return (x_dim, y_dim)
