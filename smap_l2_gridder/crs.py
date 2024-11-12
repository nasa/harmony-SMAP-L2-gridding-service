""" Module containing information particular to geolocating the input data to a target grid.

We may need to update some of these.
"""

import numpy as np

# The authoritative value is found here: https://epsg.org/crs/wkt/id/6933
# The pyproj CRS created from this string is the same as a CRS that has been
# round tripped through the CRS creation process. So the output value on the
# files CRS metadata may not match the authoritative value, but the use with
# pyproj is the same.
# i.e.
# pyproj.crs.CRS.from_wkt(epsg_6933_wkt).to_wkt() != epsg_6933_wkt
# but
# pyproj.crs.CRS.from_wkt(pyproj.crs.CRS.from_wkt(epsg_6933_wkt).to_wkt())
#   == pyproj.crs.CRS.from_wkt(epsg_6933_wkt)
epsg_6933_wkt = (
    'PROJCRS["WGS 84 / NSIDC EASE-Grid 2.0 Global",'
    'BASEGEOGCRS["WGS 84",ENSEMBLE["World Geodetic System 1984 ensemble", '
    'MEMBER["World Geodetic System 1984 (Transit)", ID["EPSG",1166]], '
    'MEMBER["World Geodetic System 1984 (G730)", ID["EPSG",1152]], '
    'MEMBER["World Geodetic System 1984 (G873)", ID["EPSG",1153]], '
    'MEMBER["World Geodetic System 1984 (G1150)", ID["EPSG",1154]], '
    'MEMBER["World Geodetic System 1984 (G1674)", ID["EPSG",1155]], '
    'MEMBER["World Geodetic System 1984 (G1762)", ID["EPSG",1156]], '
    'MEMBER["World Geodetic System 1984 (G2139)", ID["EPSG",1309]], '
    'MEMBER["World Geodetic System 1984 (G2296)", ID["EPSG",1383]], '
    'ELLIPSOID["WGS 84",6378137,298.257223563,'
    'LENGTHUNIT["metre",1,ID["EPSG",9001]],ID["EPSG",7030]], '
    'ENSEMBLEACCURACY[2],ID["EPSG",6326]],ID["EPSG",4326]],'
    'CONVERSION["US NSIDC EASE-Grid 2.0 Global",'
    'METHOD["Lambert Cylindrical Equal Area",ID["EPSG",9835]],'
    'PARAMETER["Latitude of 1st standard parallel",30,'
    'ANGLEUNIT["degree",0.0174532925199433,ID["EPSG",9102]],'
    'ID["EPSG",8823]],PARAMETER["Longitude of natural origin",0,'
    'ANGLEUNIT["degree",0.0174532925199433,ID["EPSG",9102]],'
    'ID["EPSG",8802]],PARAMETER["False easting",0,'
    'LENGTHUNIT["metre",1,ID["EPSG",9001]],ID["EPSG",8806]],'
    'PARAMETER["False northing",0,LENGTHUNIT["metre",1,ID["EPSG",9001]],'
    'ID["EPSG",8807]],ID["EPSG",6928]],CS[Cartesian,2,ID["EPSG",4499]],'
    'AXIS["Easting (X)",east],AXIS["Northing (Y)",north],'
    'LENGTHUNIT["metre",1,ID["EPSG",9001]],ID["EPSG",6933]]'
)

epsg_6931_wkt = (
    'PROJCRS["WGS 84 / NSIDC EASE-Grid 2.0 North",'
    'BASEGEOGCRS["WGS 84",ENSEMBLE["World Geodetic System 1984 ensemble", '
    'MEMBER["World Geodetic System 1984 (Transit)", ID["EPSG",1166]], '
    'MEMBER["World Geodetic System 1984 (G730)", ID["EPSG",1152]], '
    'MEMBER["World Geodetic System 1984 (G873)", ID["EPSG",1153]], '
    'MEMBER["World Geodetic System 1984 (G1150)", ID["EPSG",1154]], '
    'MEMBER["World Geodetic System 1984 (G1674)", ID["EPSG",1155]], '
    'MEMBER["World Geodetic System 1984 (G1762)", ID["EPSG",1156]], '
    'MEMBER["World Geodetic System 1984 (G2139)", ID["EPSG",1309]], '
    'MEMBER["World Geodetic System 1984 (G2296)", ID["EPSG",1383]], '
    'ELLIPSOID["WGS 84",6378137,298.257223563,LENGTHUNIT["metre",1,'
    'ID["EPSG",9001]],ID["EPSG",7030]], ENSEMBLEACCURACY[2],'
    'ID["EPSG",6326]],ID["EPSG",4326]],'
    'CONVERSION["US NSIDC EASE-Grid 2.0 North",'
    'METHOD["Lambert Azimuthal Equal Area",'
    'ID["EPSG",9820]],PARAMETER["Latitude of natural origin",90,'
    'ANGLEUNIT["degree",0.0174532925199433,ID["EPSG",9102]],ID["EPSG",8801]],'
    'PARAMETER["Longitude of natural origin",0,'
    'ANGLEUNIT["degree",0.0174532925199433,ID["EPSG",9102]],ID["EPSG",8802]],'
    'PARAMETER["False easting",0,LENGTHUNIT["metre",1,ID["EPSG",9001]],'
    'ID["EPSG",8806]],PARAMETER["False northing",0,LENGTHUNIT["metre",1,'
    'ID["EPSG",9001]],ID["EPSG",8807]],ID["EPSG",6929]],CS[Cartesian,2,'
    'ID["EPSG",4469]],AXIS["Easting (X)",South,MERIDIAN[90.0,'
    'ANGLEUNIT["degree",0.0174532925199433,ID["EPSG",9102]]]],'
    'AXIS["Northing (Y)",South,MERIDIAN[180.0,'
    'ANGLEUNIT["degree",0.0174532925199433,ID["EPSG",9102]]]],'
    'LENGTHUNIT["metre",1,ID["EPSG",9001]],ID["EPSG",6931]]'
)


EASE2_M09km = {
    'map_origin_x': -17367530.4451615,  # meters, -180.0000 deg lon  mapped to x
    'map_origin_y': 7314540.8306386,  # meters, grid map units per cell *  grid height / 2
    'grid_map_origin_column': -0.5,
    'grid_map_origin_row': -0.5,
    'grid_map_units_per_cell': 9008.055210146,  # meters, -2 * map origin x /  grid width
    'grid_width': 3856,
    'grid_height': 1624,
}


def convert_value(value: str) -> str | np.float64 | np.long:
    """Convert gpd value to appropriate type."""
    value = value.strip()
    try:
        if '.' in value:
            return np.float64(value)
        else:
            return np.long(value)
    except ValueError:
        return value

def parse_gpd_file(filename: str) -> dict:
    """
    Parse a grid parameter definition file and return a dictionary of parameters.

    Parameters:
    -----------
    filename : str
        Path to the grid parameter definition file

    Returns:
    --------
    dict
        Dictionary containing parameter names as keys and their values as values.
        Decimal numbers are converted to np.float64
        Integer-like numbers are converted to np.long
        Non-numeric values remain as strings
    """
    params = {}

    with open(filename, encoding='utf-8') as f:
        for line in f:
            # Skip empty lines and comments
            line = line.strip()
            if not line or line.startswith(';'):
                continue

            # Split on the first occurrence of ':'
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                # Remove comments and strip whitespace
                value = value.split(';')[0].strip()

                if key and value:
                    params[key] = convert_value(value)

    return params
