# smap-l2-gridder

This is a python service to transform NASA level 2 Grid trajectory data into gridded NetCDF4-CF output files.


## Transform Data

To run the regridder you can create an isolated python 3.12 environment installing packages from the `pip_requirements.txt` file.

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
