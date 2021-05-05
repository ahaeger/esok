import json
from collections import OrderedDict
from json import JSONDecodeError

import pytest
from click.testing import CliRunner
from elasticsearch import Elasticsearch, TransportError
from elasticsearch.helpers import bulk, scan

from esok.esok import esok


def test_list(runner, empty_index):
    result = runner.invoke(esok, ['index', 'list'])
    assert result.exit_code == 0
    assert 'health' in result.output
    assert empty_index in result.output


def test_touch(runner, client):
    index = 'some-index-name'
    result = runner.invoke(esok, ['index', 'touch', index])
    assert result.exit_code == 0
    assert index in client.cat.indices()


def test_touch_with_already_existing_index(runner, client, empty_index):
    result = runner.invoke(esok, ['index', 'touch', empty_index])
    assert isinstance(result.exception, TransportError)


def test_create(runner, test_app_dir, client):
    index = 'some-index'
    field_name = 'very_interesting_product_description'
    mapping = {
        '_doc': {
            'properties': {
                field_name: {
                    'type': 'text'
                }
            }
        }
    }
    mapping_file = test_app_dir / 'mapping.json'
    mapping_file.write_text(json.dumps(dict(mappings=mapping)))

    result = runner.invoke(esok, ['index', 'create', index, str(mapping_file)])

    assert result.exit_code == 0
    assert index in client.cat.indices()
    assert mapping == client.indices.get(index)[index]['mappings']


def test_create_non_existing_mapping_file(runner, test_app_dir, client):
    mapping_file = test_app_dir / 'mapping.json'
    result = runner.invoke(esok, ['index', 'create', 'some-index', str(mapping_file)])
    assert isinstance(result.exception, SystemExit)


def test_create_provided_mapping_is_directory(runner, test_app_dir, client):
    result = runner.invoke(esok, ['index', 'create', 'some-index', str(test_app_dir)])
    assert isinstance(result.exception, SystemExit)


def test_create_index_already_exists(runner, empty_index):
    result = runner.invoke(esok, ['index', 'create', 'some-index', empty_index])
    assert isinstance(result.exception, SystemExit)


def test_copy(runner, client, empty_index):
    new_index_name = 'new-index'
    result = runner.invoke(esok, ['index', 'copy', empty_index, new_index_name])

    assert result.exit_code == 0
    assert new_index_name in client.cat.indices()

    source_index = client.indices.get(empty_index)
    new_index = client.indices.get(new_index_name)
    assert _clean(source_index) == _clean(new_index)


def test_delete(runner, client, empty_index):
    result = runner.invoke(esok, ['index', 'delete', empty_index])
    assert result.exit_code == 0
    assert empty_index not in client.cat.indices()


def test_delete_non_existing_index(runner, client):
    result = runner.invoke(esok, ['index', 'delete', 'some-index'])
    assert isinstance(result.exception, TransportError)


def test_delete_aborts_by_default_on_too_broad_index_names(runner, client):
    for index_name in ['_all', '*']:
        result = runner.invoke(esok, ['index', 'delete', index_name])
        assert isinstance(result.exception, SystemExit), 'The index name "{}" should prompt for user confirmation, ' \
                                                         'and abort be default.'.format(index_name)


def test_get(runner, empty_index, client):
    result = runner.invoke(esok, ['index', 'get', empty_index])
    assert result.exit_code == 0
    assert json.loads(result.output) == client.indices.get(empty_index)


def test_stats(runner, empty_index, client):
    result = runner.invoke(esok, ['index', 'stats', empty_index])
    assert result.exit_code == 0
    assert json.loads(result.output) == client.indices.stats(empty_index)


def test_shards(runner, empty_index, client):
    result = runner.invoke(esok, ['index', 'shards', empty_index, '1'])
    assert result.exit_code == 0
    settings = client.indices.get_settings(empty_index)
    assert '0' == settings[empty_index]['settings']['index']['number_of_replicas']


def test_read(runner, filled_index):
    index_name, data = filled_index
    result = runner.invoke(esok, ['index', 'read', index_name])

    assert result.exit_code == 0
    assert result.output != '', 'Documents read should be printed to stdout.'

    results = set()
    for line in filter(lambda i: i != '', result.output.split('\n')):
        results.add(json.dumps(OrderedDict(sorted(json.loads(line)['_source'].items()))))

    assert results == set([json.dumps(OrderedDict(sorted(doc.items()))) for doc in data])


def test_write_only_data(host):
    runner = CliRunner()
    index_name = 'woot'
    input_data = [dict(title='a title'), dict(title='another title'), dict(title='the last title')]

    with runner.isolated_filesystem():
        documents_file = './docs.json'
        with open(documents_file, 'w') as f:
            f.write('\n'.join([json.dumps(doc) for doc in input_data]))

        result = runner.invoke(esok, ['index', 'write', '--refresh', '-i', index_name, documents_file])
        assert result.exit_code == 0

    client = Elasticsearch(host)
    written_data = list(scan(client, index=index_name))

    for doc in input_data:
        indexed_doc = next(filter(lambda d: d['_source'] == doc, written_data), None)
        assert indexed_doc is not None
        assert indexed_doc['_index'] == index_name
        assert indexed_doc['_type'] == '_doc'


def test_write_with_routing(host):
    runner = CliRunner()
    index_name = 'woot'
    doc_type = 'funky type'
    contents = enumerate(['a title', 'another title', 'the last title'])
    input_data = [dict(_index=index_name, _type=doc_type, _id=str(doc_id), _source=dict(title=content))
                  for doc_id, content in contents]

    with runner.isolated_filesystem():
        documents_file = './docs.json'
        with open(documents_file, 'w') as f:
            f.write('\n'.join([json.dumps(doc) for doc in input_data]))

        result = runner.invoke(esok, ['index', 'write', '--refresh', documents_file])
        assert result.exit_code == 0

    client = Elasticsearch(host)
    written_data = list(scan(client, index=index_name))

    for doc in input_data:
        doc.update(_score=None, sort=[0])
        assert doc in written_data


@pytest.mark.usefixtures('app_defaults')
def test_write_from_non_existing_file(tmp_path):
    non_existing_file = tmp_path / 'nothing_here.json'

    runner = CliRunner()
    result = runner.invoke(esok, ['index', 'write', str(non_existing_file)])

    assert isinstance(result.exception, FileNotFoundError)


@pytest.mark.usefixtures('app_defaults')
def test_write_invalid_json(tmp_path):
    invalid_json_file = tmp_path / 'invalid.json'
    invalid_json_file.write_text('this is not json')

    runner = CliRunner()
    result = runner.invoke(esok, ['index', 'write', str(invalid_json_file)])

    assert isinstance(result.exception, JSONDecodeError)


@pytest.fixture
def filled_index(host):
    index = 'test-index'
    data = [dict(title='title-%s' % i, body='body-%s' % i) for i in range(3)]
    actions = list()
    for i, doc in enumerate(data):
        action = dict(_index=index, _id=i, _type='_doc')
        action.update(dict(_source=doc))
        actions.append(action)
    client = Elasticsearch(host)
    bulk(client, actions, refresh=True)
    yield index, data


def _clean(index):
    _, index = index.copy().popitem()  # Top-level dict contains only one key, the index name
    del index['settings']['index']['version']
    del index['settings']['index']['creation_date']
    del index['settings']['index']['provided_name']
    del index['settings']['index']['uuid']
