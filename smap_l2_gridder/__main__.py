import argparse

from xarray import open_datatree

from smap_l2_gridder.grid import process_input


def parse_args():
    parser = argparse.ArgumentParser(description='PoC script to process SPL2SMP_E data')
    parser.add_argument('--input', help='Input h5 file path')
    parser.add_argument('--output', help='Output NetCDF file path')
    return parser.parse_args()

def main():
    """Entrypoint for local running and testing."""
    try:
        args = parse_args()
        with open_datatree(args.input) as in_data:
            process_input(in_data, args.output)
    except Exception as e:
        print(f"Error occurred: {e}")
        return 1
    print(f'successfully processed {args.input} into {args.output}')
    return 0

if __name__ == '__main__':
    exit(main())
