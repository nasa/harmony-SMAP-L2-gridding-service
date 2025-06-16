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


def test_get_collection_info(mocker, mock_collection_info):
    """Test getting correct collection's information."""
    mocker.patch(
        'smap_l2_gridder.collections.get_all_information',
        return_value=mock_collection_info,
    )
    expected = mock_collection_info['sample_collection']
    assert get_collection_info('sample_collection') == expected

    with pytest.raises(
        InvalidCollectionError,
        match='No collection information for invalid_collection_name',
    ):
        get_collection_info('invalid_collection_name')


def test_get_collection_group_info(mocker, mock_collection_info):
    """Check group selections return correct information."""
    mocker.patch(
        'smap_l2_gridder.collections.get_all_information',
        return_value=mock_collection_info,
    )
    expected = mock_collection_info['sample_collection']['data_groups'][
        'sample_group_name'
    ]

    assert (
        get_collection_group_info('sample_collection', 'sample_group_name') == expected
    )

    with pytest.raises(
        InvalidCollectionError,
        match='No group named invalid_sample_group in sample_collection',
    ):
        get_collection_group_info('sample_collection', 'invalid_sample_group')

    with pytest.raises(
        InvalidCollectionError,
        match='No collection information for invalid_sample_collection',
    ):
        get_collection_group_info('invalid_sample_collection', 'invalid_sample_group')


def test_get_excluded_science_variables(mocker, mock_collection_info):
    """Test dropped variable functionality."""
    mocker.patch(
        'smap_l2_gridder.collections.get_all_information',
        return_value=mock_collection_info,
    )

    expected = set(['hot-variable1', 'hot-variable2'])
    assert (
        get_excluded_science_variables('sample2_collection', 'dropped_group_name')
        == expected
    )

    expected = set()
    assert (
        get_excluded_science_variables('sample_collection', 'sample_group_name')
        == expected
    )

    with pytest.raises(
        InvalidCollectionError,
        match='No collection information for invalid_collection_name',
    ):
        get_excluded_science_variables('invalid_collection_name', 'group')


def test_get_flattened_variables(mocker, mock_collection_info):
    """Test checking configuration for flattening."""
    mocker.patch(
        'smap_l2_gridder.collections.get_all_information',
        return_value=mock_collection_info,
    )

    assert (
        get_flattened_variables('sample_collection', 'sample_group_name', {'anything'})
        == set()
    )

    assert get_flattened_variables(
        'sample_collection',
        'group_with_flattened_vars',
        {'anything', 'smashed-var1', 'smashed-var2'},
    ) == {'smashed-var1', 'smashed-var2'}

    assert get_flattened_variables(
        'sample_collection', 'group_with_flattened_vars', {'anything', 'smashed-var2'}
    ) == {'smashed-var2'}
