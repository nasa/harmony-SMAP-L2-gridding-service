"""Tests for the provenance module."""

import json
from datetime import datetime

import pytest
from xarray import DataTree

from smap_l2_gridder import provenance
from smap_l2_gridder.provenance import (
    HISTORY_JSON_SCHEMA,
    PROGRAM,
    PROGRAM_REF,
    create_history_json_record,
    get_request_url_attribute,
    get_semantic_version,
    read_history_attrs,
    read_history_json_attrs,
    update_history_metadata,
)


@pytest.fixture
def existing_history_json_record():
    """Upstream history_json pseudo-record from a Hyrax-subsetted SMAP granule."""
    return {
        '$schema': 'https://harmony.earthdata.nasa.gov/schemas/history/0.1.0/history-0.1.0.json',
        'date_time': '2025-04-22T22:49:46.867+0000',
        'program': 'hyrax',
        'version': '1.17.1-89',
        'parameters': [
            {
                'request_url': (
                    'https://opendap.uat.earthdata.nasa.gov/collections/'
                    'C1268617120-EEDTEST/granules/SC:SPL3FTP.004:296000481.dap.nc4'
                    '?A-api-request-uuid=8c4abeea-0cd4-4332-bc60-5d7baeb8bc7e'
                    ',dap4.ce=%2FFreeze_Thaw_Retrieval_Data_Global%2Fsurface_flag'
                )
            },
        ],
    }


def test_get_semantic_version():
    """The version is read from docker/service_version.txt."""
    version = get_semantic_version()
    assert isinstance(version, str)
    assert version != ''
    # Sanity check it looks like a semantic version (major.minor.patch).
    assert len(version.split('.')) == 3


def test_create_history_json_record():
    """A history_json record contains the expected provenance fields."""
    record = create_history_json_record('https://example.com/granule.h5')

    assert record['$schema'] == HISTORY_JSON_SCHEMA
    assert record['program'] == PROGRAM
    assert record['program_ref'] == PROGRAM_REF
    assert record['version'] == get_semantic_version()
    assert record['derived_from'] == 'https://example.com/granule.h5'
    # date_time is a valid ISO-8601 timestamp.
    assert datetime.fromisoformat(record['date_time'])


def test_read_history_attrs_lowercase():
    """A lowercase `history` attribute is detected and returned."""
    dt = DataTree()
    dt.attrs['history'] = 'existing history line'
    assert read_history_attrs(dt) == ('history', 'existing history line')


def test_read_history_attrs_capitalized():
    """A capitalized `History` attribute is detected and its casing preserved."""
    dt = DataTree()
    dt.attrs['History'] = 'existing History line'
    assert read_history_attrs(dt) == ('History', 'existing History line')


def test_read_history_attrs_absent():
    """When no history attribute exists the name defaults to `history`."""
    assert read_history_attrs(DataTree()) == ('history', None)


def test_read_history_json_attrs_absent():
    """A missing history_json normalizes to an empty list."""
    assert read_history_json_attrs(DataTree()) == []


def test_read_history_json_attrs_single_object(existing_history_json_record):
    """A single history_json object is normalized into a one-element list."""
    dt = DataTree()
    dt.attrs['history_json'] = json.dumps(existing_history_json_record)
    assert read_history_json_attrs(dt) == [existing_history_json_record]


def test_read_history_json_attrs_list(existing_history_json_record):
    """A history_json list is returned as-is."""
    dt = DataTree()
    dt.attrs['history_json'] = json.dumps([existing_history_json_record])
    assert read_history_json_attrs(dt) == [existing_history_json_record]


def test_get_request_url_attribute_absent():
    """Without history_json, the input file name is the fallback."""
    assert get_request_url_attribute(DataTree(), 'input.h5') == 'input.h5'


def test_get_request_url_attribute_from_list(existing_history_json_record):
    """The request_url is extracted from list parameters and stripped of query."""
    dt = DataTree()
    dt.attrs['history_json'] = json.dumps([existing_history_json_record])
    assert get_request_url_attribute(dt, 'input.h5') == (
        'https://opendap.uat.earthdata.nasa.gov/collections/'
        'C1268617120-EEDTEST/granules/SC:SPL3FTP.004:296000481.dap.nc4'
    )


def test_get_request_url_attribute_from_dict():
    """The request_url is extracted from dict parameters."""
    dt = DataTree()
    dt.attrs['history_json'] = json.dumps(
        {'parameters': {'request_url': 'https://example.com/g.h5?ce=1'}}
    )
    assert get_request_url_attribute(dt, 'input.h5') == 'https://example.com/g.h5'


def test_get_request_url_attribute_no_request_url():
    """Without a request_url the input file name is the fallback."""
    dt = DataTree()
    dt.attrs['history_json'] = json.dumps({'parameters': {'other': 'value'}})
    assert get_request_url_attribute(dt, 'input.h5') == 'input.h5'


def test_update_history_metadata_no_existing_history():
    """A clean input gains a history line and a one-record history_json."""
    in_data = DataTree()
    out_data = DataTree()

    update_history_metadata(in_data, out_data, 'input.h5')

    history_json = json.loads(out_data.attrs['history_json'])
    assert len(history_json) == 1
    assert history_json[0]['program'] == PROGRAM
    assert history_json[0]['derived_from'] == 'input.h5'

    # The human-readable history is the single new line.
    assert PROGRAM in out_data.attrs['history']
    assert out_data.attrs['history'].count('\n') == 0


def test_update_history_metadata_appends_existing(existing_history_json_record):
    """Existing provenance is preserved and the new record appended."""
    in_data = DataTree()
    in_data.attrs['history'] = '2026-01-29 hyrax 1.17.1-560'
    in_data.attrs['history_json'] = json.dumps([existing_history_json_record])
    out_data = DataTree()

    update_history_metadata(in_data, out_data, 'input.h5')

    history_json = json.loads(out_data.attrs['history_json'])
    assert len(history_json) == 2
    assert history_json[0] == existing_history_json_record
    assert history_json[1]['program'] == PROGRAM
    # derived_from comes from the upstream request_url, query stripped.
    assert history_json[1]['derived_from'].endswith('296000481.dap.nc4')

    # The new line is appended below the existing history text.
    history_lines = out_data.attrs['history'].split('\n')
    assert len(history_lines) == 2
    assert history_lines[0] == '2026-01-29 hyrax 1.17.1-560'
    assert PROGRAM in history_lines[1]


def test_update_history_metadata_preserves_history_casing():
    """A capitalized `History` attribute keeps its casing in the output."""
    in_data = DataTree()
    in_data.attrs['History'] = 'old History'
    out_data = DataTree()

    update_history_metadata(in_data, out_data, 'input.h5')

    assert 'History' in out_data.attrs
    assert 'history' not in out_data.attrs


def test_get_semantic_version_missing_file(monkeypatch, tmp_path):
    """A missing version file raises rather than silently returning bad data."""
    monkeypatch.setattr(provenance, 'VERSION_FILE', tmp_path / 'does_not_exist.txt')
    with pytest.raises(FileNotFoundError):
        get_semantic_version()
