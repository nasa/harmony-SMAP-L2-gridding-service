"""Test the collection configuration module."""

import pytest

from smap_l2_gridder.collections import (
    InvalidCollectionError,
    get_collection_group_info,
    get_collection_info,
    get_excluded_science_variables,
    get_flattened_variables,
)


@pytest.fixture
def mock_collection_info():
    """Fake collection information for testing."""
    return {
        'sample_collection': {
            'metadata': ['Metadata'],
            'data_groups': {
                'sample_group_name': {
                    'row': 'path/to/row',
                    'col': 'path/to/col',
                    'gpd': 'test.gpd',
                    'epsg': 'EPSG:test',
                },
                'group_with_flattened_vars': {
                    'row': 'path/to/row',
                    'col': 'path/to/col',
                    'gpd': 'test.gpd',
                    'epsg': 'EPSG:test',
                    'FlattenedVariables': ['smashed-var1', 'smashed-var2'],
                },
            },
        },
        'sample2_collection': {
            'metadata': ['Metadata'],
            'data_groups': {
                'dropped_group_name': {
                    'row': 'path/to/row',
                    'col': 'path/to/col',
                    'gpd': 'test.gpd',
                    'epsg': 'EPSG:test',
                    'ExcludedScienceVariables': ['hot-variable1', 'hot-variable2'],
                }
            },
        },
    }


@pytest.fixture
def mock_get_all_information(mocker, mock_collection_info):
    """Mock the collections.get_all_information function with test data."""
    return mocker.patch(
        'smap_l2_gridder.collections.get_all_information',
        return_value=mock_collection_info,
    )


def test_get_collection_info(mock_collection_info, mock_get_all_information):
    """Test getting correct collection's information."""
    expected = mock_collection_info['sample_collection']
    assert get_collection_info('sample_collection') == expected


def test_get_collection_info_raises_invalid_collection(mock_get_all_information):
    """Test raises for invalid collection name."""
    with pytest.raises(
        InvalidCollectionError,
        match='No collection information for invalid_collection_name',
    ):
        get_collection_info('invalid_collection_name')


def test_get_collection_group_info(mock_collection_info, mock_get_all_information):
    """Check group selections return correct information."""
    expected = mock_collection_info['sample_collection']['data_groups'][
        'sample_group_name'
    ]

    assert (
        get_collection_group_info('sample_collection', 'sample_group_name') == expected
    )


def test_get_collection_group_info_raises_with_invalid_group(mock_get_all_information):
    """Test raises invalid group."""
    with pytest.raises(
        InvalidCollectionError,
        match='No group named invalid_sample_group in sample_collection',
    ):
        get_collection_group_info('sample_collection', 'invalid_sample_group')


def test_get_collection_group_info_raises_with_invalid_collection(
    mock_get_all_information,
):
    """Test raises invalid group."""
    with pytest.raises(
        InvalidCollectionError,
        match='No collection information for invalid_sample_collection',
    ):
        get_collection_group_info('invalid_sample_collection', 'invalid_sample_group')


def test_get_excluded_science_variables_dropped_variable(mock_get_all_information):
    """Test dropped variable functionality."""
    expected = set(['hot-variable1', 'hot-variable2'])
    assert (
        get_excluded_science_variables('sample2_collection', 'dropped_group_name')
        == expected
    )


def test_get_excluded_science_variables_none_to_exclude(mock_get_all_information):
    """Test no excluded variables."""
    expected = set()
    assert (
        get_excluded_science_variables('sample_collection', 'sample_group_name')
        == expected
    )


def test_get_excluded_science_variables_no_collections(mock_get_all_information):
    """Test raises for invalid collection name."""
    with pytest.raises(
        InvalidCollectionError,
        match='No collection information for invalid_collection_name',
    ):
        get_excluded_science_variables('invalid_collection_name', 'group')


def test_get_flattened_variables_no_flattening_available(mock_get_all_information):
    """Test flattening without any available in config."""
    actual_flattened = get_flattened_variables(
        'sample_collection', 'sample_group_name', {'anything'}
    )
    assert actual_flattened == set()


def test_get_flattened_variables_flattening_available(mock_get_all_information):
    """Test for vars flattend and in the source file."""
    actual_flattening = get_flattened_variables(
        'sample_collection',
        'group_with_flattened_vars',
        {'anything', 'smashed-var1', 'smashed-var2'},
    )
    assert actual_flattening == {'smashed-var1', 'smashed-var2'}


def test_get_flattened_variables_flattening_available_missing_in_source(
    mock_get_all_information,
):
    """Test multiple flattening possible, only one in source."""
    actual_flattening = get_flattened_variables(
        'sample_collection', 'group_with_flattened_vars', {'anything', 'smashed-var2'}
    )
    assert actual_flattening == {'smashed-var2'}
