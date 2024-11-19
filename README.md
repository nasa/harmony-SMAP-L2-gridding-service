# smap-l2-gridder

This is a python service to transform NASA level 2 Grid trajectory data into gridded NetCDF4-CF output files.


## Transform Data

To run the regridder you can create an isolated python 3.12 environment installing packages from the `pip_requirements.txt` file.

From the commandline run:

```python
python -m smap_l2_gridder --input path/to/granule.h5 --output path/to/output_granule.nc
```
