# SMAP L2 Gridding Service

This repository contains the code for the SMAP-L2-Gridding-Service, which is a python service that transforms NASA level 2 gridded trajectory data into gridded NetCDF4-CF output files.

This code currently works on `SPL2SMP_E` data and will be adapted for other SMAP collections of gridded trajectory data.


## Transforming Data

The logic of transforming data is contained in the `smap_l2_gridder` directory. It reads NASA L2 Gridded trajectory data and writes output NetCDF-CF files with the trajecotry style data correctly populated into EASE2 grids.

### Commandline invocation
To run the regridder on an input file.  Create an isolated python 3.12 environment using packages from the `pip_requirements.txt` file and then from the commandline run:

```python
python -m smap_l2_gridder --input path/to/granule.h5 --output path/to/output_granule.nc
```

`smap_l2_gridder/__main__.py` is the entrypoint to the science logic module and can be used for testing and development.

## Directory structure

```
📁
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── 📁 bin
├── 📁 docker
├── 📁 harmony_service
├── pip_requirements.txt
├── pyproject.toml
├── 📁 smap_l2_gridder
└── 📁 tests
```

* `CHANGELOG.md` -   Contains a record of changes applied to each new release of the SMAP-L2-Gridding-Service.
* `CONTRIBUTING.md` -  Instructions on how to contribute to the repository.
* `LICENSE` - Required for distribution under NASA open-source approval. Details conditions for use, reproduction and distribution.
* `README.md` - This file, containing guidance on developing the library and service.
* `bin` - A directory containing utility scripts to build the service and test images. A script to extract the release notes for the most recent version, as contained in `CHANGELOG.md` is also in this directory.
* `docker` - A directory containing the Dockerfiles for the service and test images. It also contains `service_version.txt`, which contains the semantic version number of the library and service image. Update this file with a new version to trigger a release.
*  `harmony_service` - A directory containing the Harmony Service specific python code. `adapter.py` contains the `SMAPL2GridderAdapter` class that is invoked by calls to the Harmony service.
* `pip_requirements.txt` - Contains a list of python packages needed to run the service.
* `pyproject.toml` - Configuration file used by packaging tools, and other tools such as linters, type checkers, etc.
* `smap_l2_gridder` - Python package containing the logic for reformatting L2G data.
* `tests` -  Contains the pytest test suite.


## `pre-commit` hooks

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
