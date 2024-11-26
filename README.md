# SMAP L2 Gridding Service

This repository contains the code for the SMAP-L2-Gridding-Service, which is a python service that transforms NASA level 2 gridded trajectory data into gridded NetCDF4-CF output files.

This code currently works on `SPL2SMP_E` data and will be adapted for other gridded trajectory data.






## Transform Data
To run the regridder, first create an isolated python 3.12 environment using packages from the `pip_requirements.txt` file.

From the commandline run:

```python
python -m smap_l2_gridder --input path/to/granule.h5 --output path/to/output_granule.nc
```


## pre-commit hooks:

This repository uses [pre-commit](https://pre-commit.com/) to enable pre-commit
checks that enforce coding standard best practices. These include:

* Removing trailing whitespaces.
* Removing blank lines at the end of a file.
* Ensure JSON files have valid formats.
* [ruff](https://github.com/astral-sh/ruff) Python linting checks.
* [black](https://black.readthedocs.io/en/stable/index.html) Python code
  formatting checks.

To enable these checks:

```bash
# Install pre-commit Python package:
pip install pre-commit

# Install the git hook scripts:
pre-commit install
```
