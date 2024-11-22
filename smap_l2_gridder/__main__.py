"""Module to allow running from a commandline."""

import argparse
from pathlib import Path

from xarray import open_datatree

from smap_l2_gridder.grid import process_input


def parse_args():
    """Get input and output filenames from args."""
    parser = argparse.ArgumentParser(description='PoC script to process SPL2SMP_E data')
    parser.add_argument('--input', help='Input h5 file path')
    parser.add_argument('--output', help='Output NetCDF file path')
    return parser.parse_args()


def main():
    """Entrypoint for local running and testing."""
    try:
        args = parse_args()
        with open_datatree(args.input, decode_times=False) as in_data:
            process_input(in_data, Path(args.output))
    except Exception as e:
        print(f"Error occurred: {e}")
        raise e
    print(f'successfully processed {args.input} into {args.output}')
    return 0


if __name__ == '__main__':
    main()
