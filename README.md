# Harmony SMAP L2 Gridding Service

This repository contains the code for the Harmony-SMAP-L2-Gridding-Service, which is a python service that transforms NASA level 2 gridded trajectory data into gridded NetCDF4-CF output files.

This code currently works on `SPL2SMP_E`, and `SPL2SMAP`, `SPL2SMP`, and `SPL2SMA` collections of gridded trajectory data.


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
├── 📁 docs
├── 📁 harmony_service
├── pip_requirements.txt
├── pyproject.toml
├── 📁 smap_l2_gridder
└── 📁 tests
```

* `CHANGELOG.md` -   Contains a record of changes applied to each new release of the Harmony-SMAP-L2-Gridding-Service.
* `CONTRIBUTING.md` -  Instructions on how to contribute to the repository.
* `LICENSE` - Required for distribution under NASA open-source approval. Details conditions for use, reproduction and distribution.
* `README.md` - This file, containing guidance on developing the library and service.
* `bin` - A directory containing utility scripts to build the service and test images. A script to extract the release notes for the most recent version, as contained in `CHANGELOG.md` is also in this directory.
* `docker` - A directory containing the Dockerfiles for the service and test images. It also contains `service_version.txt`, which contains the semantic version number of the library and service image. Update this file with a new version to trigger a release.
* `docs` - A directory containing an example notebook demonstrating how to use the service and examining the service output data.
*  `harmony_service` - A directory containing the Harmony Service specific python code. `adapter.py` contains the `SMAPL2GridderAdapter` class that is invoked by calls to the Harmony service.
* `pip_requirements.txt` - Contains a list of python packages needed to run the service.
* `pyproject.toml` - Configuration file used by packaging tools, and other tools such as linters, type checkers, etc.
* `smap_l2_gridder` - Python package containing the logic for reformatting L2G data.
* `tests` -  Contains the pytest test suite.


## Local development

Local testing of service functionality can be achieved via a local instance of
[Harmony](https://github.com/nasa/harmony) aka Harmony-In-A-Box. Please see instructions there
regarding creation of a local Harmony instance.

For local development and testing of library modifications or small functions independent of the main Harmony application:

1. Create a Python virtual environment
1. Install the dependencies in `pip_requirements.txt`, and `tests/pip_test_requirements.txt`
1. Install the pre-commit hooks ([described below](#pre-commit-hooks)).


## Tests

This service utilises the Python `pytest` package to perform unit tests on
classes and functions in the service. After local development is complete, and
test have been updated, they can be run in Docker via:

```bash
$ ./bin/build-image
$ ./bin/build-test
$ ./bin/run-test
```

It is also possible to run the test scripts directly (without docker) by just running the `run_tests.sh` script with a proper python environment. Do note that the `reports` directory will appear in the directory you call the script from.

The `tests/run_tests.sh` script will also generate a coverage report, rendered
in HTML, and scan the code with `pylint`.

The `pytest` suite is run automatically within a GitHub workflow as part of a
CI/CD pipeline. These tests are run for all changes made in a PR against the
`main` branch. The tests must pass in order to merge the PR.

## `pre-commit` hooks

This repository uses [pre-commit](https://pre-commit.com/) to enable pre-commit
checks that enforce coding standard best practices. These include:

* Removing trailing whitespaces.
* Removing blank lines at the end of a file.
* Ensure JSON files have valid formats.
* [ruff](https://github.com/astral-sh/ruff) Python linting checks.
* [black](https://black.readthedocs.io/en/stable/index.html) Python code
  formatting checks.

To enable these checks locally:

```bash
# Install pre-commit Python package:
pip install pre-commit

# Install the git hook scripts:
pre-commit install
```

## Versioning

Docker service images for the `harmony-smap-l2-gridder` adhere to [semantic
version](https://semver.org/) numbers: major.minor.patch.

* Major increments: These are non-backwards compatible API changes.
* Minor increments: These are backwards compatible API changes.
* Patch increments: These updates do not affect the API to the service.

## CI/CD

The CI/CD for Harmony-SMAP-L2-Gridding-Service is run on github actions with
the workflows in the `.github/workflows` directory:

* `run_lib_tests.yml` - A reusable workflow that tests the library functions
  against the supported python versions.
* `run_service_tests.yml` - A reusable workflow that builds the service and
  test Docker images, then runs the Python unit test suite in an instance of
  the test Docker container.
* `run_tests_on_pull_requests.yml` - Triggered for all PRs against the `main`
  branch. It runs the workflow in `run_service_tests.yml` and
  `run_lib_tests.yml` to ensure all tests pass for the new code.
* `publish_docker_image.yml` - Triggered either manually or for commits to the
  `main` branch that contain changes to the `docker/service_version.txt` file.
* `publish_release.yml`<a name="release-workflow"></a> - workflow runs
   automatically when there is a change to the `docker/service_version.txt`
   file on the main branch.  This workflow will:
    * Run the full unit test suite, to prevent publication of broken code.
    * Extract the semantic version number from `docker/service_version.txt`.
    * Extract the released notes for the most recent version from `CHANGELOG.md`.
    * Build and deploy a this service's docker image to `ghcr.io`.
    * Publish a GitHub release under the semantic version number, with associated
      git tag.


## Releasing

A release consists of a new Docker image for the Harmony SMAP L2 gridding service
published to github's container repository.

A release is made automatically when a commit to the `main` branch contains a
changes in the `docker/service_version.txt` file, see the [publish_release](#release-workflow) workflow in the CI/CD section above.

Before **merging** a PR that will trigger a release, ensure these two files are updated:

* `CHANGELOG.md` - Notes should be added to capture the changes to the service and a link to the current pull request should be included.
* `docker/service_version.txt` - The semantic version number should be updated to trigger the release.

The `CHANGELOG.md` file requires a specific format for a new release, as it
looks for the following string to define the newest release of the code
(starting at the top of the file).

```
## [vX.Y.Z] - YYYY-MM-DD
```

Where the markdown reference needs to be updated at the bottom of the file following the existing pattern.
```
[vX.Y.Z]: https://github.com/nasa/harmony-SMAP-L2-gridding-service/releases/tag/X.Y.Z
```
