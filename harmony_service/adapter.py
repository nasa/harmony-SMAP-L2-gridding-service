"""`HarmonyAdapter` for SMAP-L2-Gridding-Service.

The class in this file is the top level of abstraction for a service that will
accept an input L2G input granule and transform it into a fully gridded
NetCDF-CF output file

Currently, the service works with SPL2SMP_E granules.

"""

from pathlib import Path
from tempfile import TemporaryDirectory

from harmony_service_lib import BaseHarmonyAdapter
from harmony_service_lib.message import Source as HarmonySource
from harmony_service_lib.util import download, generate_output_filename, stage
from pystac import Asset, Item

from smap_l2_gridder.grid import transform_l2g_input


class SMAPL2GridderAdapter(BaseHarmonyAdapter):
    """Custom adapter for Harmony-SMAP-L2-Gridder Service."""

    def process_item(self, item: Item, source: HarmonySource) -> Item:
        """Process single input STAC item."""
        with TemporaryDirectory() as working_directory:
            try:
                results = item.clone()
                results.assets = {}

                asset = next(
                    item_asset
                    for item_asset in item.assets.values()
                    if 'data' in (item_asset.roles or [])
                )

                # Download the input:
                input_filepath = download(
                    asset.href,
                    working_directory,
                    logger=self.logger,
                    cfg=self.config,
                    access_token=self.message.accessToken,
                )

                working_filename = Path(input_filepath).parent / 'working_gridded.nc'

                final_target_filename = generate_output_filename(
                    asset.href, is_regridded=True, ext='.nc'
                )

                transform_l2g_input(
                    input_filepath, working_filename, logger=self.logger
                )

                # Stage the transformed output:
                staged_url = stage(
                    working_filename,
                    final_target_filename,
                    'application/x-netcdf4',
                    location=self.message.stagingLocation,
                    logger=self.logger,
                    cfg=self.config,
                )

                # Add the asset to the results Item
                results.assets['data'] = Asset(
                    staged_url,
                    title=Path(staged_url).name,
                    media_type='application/x-netcdf4',
                    roles=['data'],
                )
                return results

            except Exception as exception:
                self.logger.exception(exception)
                raise exception
