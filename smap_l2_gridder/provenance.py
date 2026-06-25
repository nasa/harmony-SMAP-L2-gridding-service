"""Functions for writing provenance metadata to gridded output.

To adhere to TRT-42 (consistent provenance metadata in NetCDF transformed file
outputs), the SMAP L2 Gridder records both a human-readable `history` (or
`History`) global attribute and a structured `history_json` global attribute on
the output file. These describe the service that produced the file, its
version, and the time of processing, and they preserve any provenance that was
already present on the input granule.

"""

import json
from datetime import datetime, timezone
from pathlib import Path

from xarray import DataTree

# Values needed for the history_json attribute.
HISTORY_JSON_SCHEMA = (
    'https://harmony.earthdata.nasa.gov/schemas/history/0.1.0/history-v0.1.0.json'
)
PROGRAM = 'Harmony SMAP L2 Gridder'
PROGRAM_REF = 'https://github.com/nasa/harmony-SMAP-L2-gridding-service'
VERSION_FILE = Path(__file__).resolve().parent.parent / 'docker' / 'service_version.txt'


def update_history_metadata(
    input_data: DataTree, output_data: DataTree, input_file_name: str
) -> DataTree:
    """Add provenance metadata describing this gridding operation.

    Reads any existing `history`/`history_json` provenance from the input
    granule, appends a record for the current SMAP L2 Gridder operation, and
    writes the combined provenance onto the (freshly built) output DataTree.

    Two forms of history metadata are written to the root of `output_data`:

    • `history_json` - a JSON string containing the structured provenance
      records. Existing records from the input granule are preserved and the
      new gridding record is appended.

    • `history` (or `History`, matching whichever the input used) - a
      newline-delimited, human-readable summary. The new gridding entry is
      appended to any pre-existing history text.

    Args:
        input_data: The input granule DataTree, read for existing provenance.
        output_data: The output DataTree onto which provenance is written.
        input_file_name: Path to the input granule, used as a fallback
            `derived_from` value when no upstream request URL is available.

    Returns:
        The `output_data` DataTree, with provenance attributes added to its
        root.
    """
    history_attribute_name, existing_history = read_history_attrs(input_data)

    request_url = get_request_url_attribute(input_data, input_file_name)

    new_history_json_record = create_history_json_record(request_url)

    output_history_json = read_history_json_attrs(input_data)
    output_history_json.append(new_history_json_record)
    output_data.attrs['history_json'] = json.dumps(output_history_json)

    new_history_line = ' '.join(
        [
            new_history_json_record['date_time'],
            new_history_json_record['program'],
            new_history_json_record['version'],
        ]
    )
    output_data.attrs[history_attribute_name] = '\n'.join(
        filter(None, [existing_history, new_history_line])
    )

    return output_data


def read_history_attrs(datatree: DataTree) -> tuple[str, str | None]:
    """Return the history attribute name in use and its existing value.

    Both `History` and `history` are seen in the wild. The casing of the input
    is preserved so the output does not end up with two competing attributes.

    Args:
        datatree: DataTree whose root attributes are inspected.

    Returns:
        A tuple of (attribute_name, existing_value). When no history attribute
        is present the name defaults to `history` and the value to None.
    """
    if 'History' in datatree.attrs:
        return 'History', datatree.attrs['History']
    if 'history' in datatree.attrs:
        return 'history', datatree.attrs['history']
    return 'history', None


def read_history_json_attrs(datatree: DataTree) -> list:
    """Return the existing `history_json` records as a list.

    The `history_json` attribute may be absent, a single record object, or a
    list of records. The return value is always normalized to a list so the new
    record can simply be appended.

    Args:
        datatree: DataTree whose root attributes are inspected.

    Returns:
        A list of existing `history_json` records, or an empty list when the
        attribute is absent.
    """
    if 'history_json' not in datatree.attrs:
        return []

    existing_history_json = json.loads(datatree.attrs['history_json'])
    if isinstance(existing_history_json, list):
        return existing_history_json
    return [existing_history_json]


def get_request_url_attribute(datatree: DataTree, input_file_name: str) -> str:
    """Extract the source granule URL from the input's `history_json`.

    Reads the input granule's `history_json` attribute, if present, and returns
    the `request_url` recorded by an upstream service (for example, the OPeNDAP
    request that produced the input). Any query string is stripped. When no
    `history_json` or `request_url` is available, the input file name is
    returned as a fallback.

    Args:
        datatree: The input granule DataTree.
        input_file_name: Fallback value used when no request URL is found.

    Returns:
        The source granule URL without query parameters, or `input_file_name`.
    """
    if 'history_json' not in datatree.attrs:
        return input_file_name

    history_json = json.loads(datatree.attrs['history_json'])
    if isinstance(history_json, list):
        history_json = history_json[0]

    parameters = history_json.get('parameters')

    if isinstance(parameters, dict) and 'request_url' in parameters:
        return parameters['request_url'].split('?', 1)[0]

    if isinstance(parameters, list):
        for item in parameters:
            if isinstance(item, dict) and 'request_url' in item:
                return item['request_url'].split('?', 1)[0]

    return input_file_name


def create_history_json_record(granule_url: str) -> dict:
    """Build a single `history_json` record for this gridding operation.

    Args:
        granule_url: The source granule the output is derived from. Stored in
            the `derived_from` field.

    Returns:
        A dictionary describing the operation, ready to be serialized into the
        `history_json` attribute.
    """
    return {
        '$schema': HISTORY_JSON_SCHEMA,
        'date_time': datetime.now(timezone.utc).isoformat(),
        'program': PROGRAM,
        'version': get_semantic_version(),
        'derived_from': granule_url,
        'program_ref': PROGRAM_REF,
    }


def get_semantic_version() -> str:
    """Return the service semantic version from `docker/service_version.txt`."""
    return VERSION_FILE.read_text(encoding='utf-8').strip()
