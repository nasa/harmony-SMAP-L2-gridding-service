# Reference files for Harmony SMAP L2 gridding service

These are copies of the gpd files describing the EASE2 grids copied directly from the [mapxmaps NSIDC repository](https://github.com/nsidc/mapxmaps).

These files are stable and do not change regularly (over 13 years for M09 and
N09). Rather than use a gitsubmodule, I have chosen to copy the files to
prevent adding unnecessary complexity.  I could have copied the information
into python dictionaries, but parsing these files and working with them
directly will ease the burden of verifying that we haven't missed anything.
Hopefully someday we well be able to work with the files directly online.
