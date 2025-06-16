# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.4.0] - 2025-06-16

### Added

- Adds example notebook to demonstrate the service and examine the output data.

### Fixed

- Fixes bug for SPL2SMP requests that occurred when a SMAP-L2-Gridding request was preceeded by a HOSS variable subset request ([DAS-2383](https://bugs.earthdata.nasa.gov/browse/DAS-2383)).  Two dimensional variables in the collection are now checked to ensure they are in the input file before we try to flatten them.

## [v0.3.0] - 2025-02-17

### Added

- Adds support for SPL2SMP ([SMAP L2 Radiometer Half-Orbit 36 km EASE-Grid Soil Moisture, Version 9](https://nsidc.org/data/spl2smp/versions/9)).
  The 2D input variables `landcover_class` and `landcover_class_fraction` are separated into 3 1D variables before gridding.
  `tb_time_utc` is dropped in the output and can be derived from `tb_time_seconds`


## [v0.2.1] - 2025-02-06

### Changed

- Output file written incrementally to reduce total memory usage.


## [v0.2.0] - 2025-02-04

### Added

- Adds support for SPL2SMA ([SMAP L2 Radar Half-Orbit 3 km EASE-Grid Soil Moisture, Version 3](https://nsidc.org/data/spl2sma/versions/3)).


## [v0.1.0] - 2025-01-21

### Added

- Adds support for SPL2SMAP ([SMAP L2 Radar/Radiometer Half-Orbit 9 km EASE-Grid Soil Moisture](https://nsidc.org/data/spl2smap/versions/3)).
- Removes `tb_time_utc` variables from SPL2SMP_E output.


## [v0.0.4] - 2024-12-04

### Changed

- Docker images are renamed to `harmony-smap-l2-gridder` [#8](https://github.com/nasa/harmony-SMAP-L2-gridding-service/pull/8)

## [v0.0.2] - 2024-12-03

### Changed

- Docker images now use full repository name [#7](https://github.com/nasa/harmony-SMAP-L2-gridding-service/pull/7)

## [v0.0.1] - 2024-11-27

### Added

- Initial codebase that transforms SPL2SMP_E granules into NetCDF4-CF grids [#1](https://github.com/nasa/harmony-SMAP-L2-gridding-service/pull/1)
- Code and configuration to wrap gridding logic into a Harmony Service [#3](https://github.com/nasa/harmony-SMAP-L2-gridding-service/pull/3 )
- GitHub actions CI configuration [#4](https://github.com/nasa/harmony-SMAP-L2-gridding-service/pull/4 )

[v0.4.0]: https://github.com/nasa/harmony-SMAP-L2-gridding-service/releases/tag/0.4.0
[v0.3.0]: https://github.com/nasa/harmony-SMAP-L2-gridding-service/releases/tag/0.3.0
[v0.2.1]: https://github.com/nasa/harmony-SMAP-L2-gridding-service/releases/tag/0.2.1
[v0.2.0]: https://github.com/nasa/harmony-SMAP-L2-gridding-service/releases/tag/0.2.0
[v0.1.0]: https://github.com/nasa/harmony-SMAP-L2-gridding-service/releases/tag/0.1.0
[v0.0.4]: https://github.com/nasa/harmony-SMAP-L2-gridding-service/releases/tag/0.0.4
[v0.0.2]: https://github.com/nasa/harmony-SMAP-L2-gridding-service/releases/tag/0.0.2
[v0.0.1]: https://github.com/nasa/harmony-SMAP-L2-gridding-service/releases/tag/0.0.1
