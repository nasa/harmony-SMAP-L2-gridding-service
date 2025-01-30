# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[v0.0.4]: https://github.com/nasa/harmony-SMAP-L2-gridding-service/releases/tag/0.0.4
[v0.0.2]: https://github.com/nasa/harmony-SMAP-L2-gridding-service/releases/tag/0.0.2
[v0.0.1]: https://github.com/nasa/harmony-SMAP-L2-gridding-service/releases/tag/0.0.1
