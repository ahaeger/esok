import os
from urllib.parse import urlparse

import pytest
from click.testing import CliRunner
from elasticsearch import Elasticsearch, TransportError
from testcontainers.elasticsearch import ElasticsearchContainer


@pytest.fixture(autouse=True)
def test_app_dir(monkeypatch, tmp_path):
    """ Ensures that tests uses a temporary app directory. """
    monkeypatch.setattr('click.get_app_dir', lambda *args, **kwargs: str(tmp_path))
    yield tmp_path


@pytest.fixture
def user_config_file(test_app_dir):
    conf = test_app_dir / 'esok.ini'
    yield conf


@pytest.fixture(scope='session')
def es_instance():
    """ Returns hostname:port of a running ES instance. """
    external_host = os.environ.get('ELASTICSEARCH_HOST')
    if external_host is not None:
        yield external_host
    else:
        with ElasticsearchContainer(image='elasticsearch:6.6.1') as es:
            url = urlparse(es.get_url())
            yield '{}:{}'.format(url.hostname, url.port)


@pytest.fixture(scope='session')
def _client(es_instance):
    yield Elasticsearch(es_instance)


@pytest.fixture
def es_cleaned(es_instance, _client):
    """ Pass-through of es_instance, but ensures ES is cleaned on every test invocation. """
    try:
        _client.indices.delete('_all')
    except TransportError as e:
        raise Exception('Could not clean ES.') from e
    yield es_instance


@pytest.fixture
def default_config_file(test_app_dir, es_cleaned):
    config = '[general]\ndefault_connection = {}\n'.format(es_cleaned)
    config_file = test_app_dir / 'esok.ini'
    config_file.write_text(config)
    yield config_file


@pytest.fixture
def app_defaults(default_config_file, es_cleaned):
    """ Sets up config file with default_host pointing towards running ES instance. """
    yield es_cleaned


@pytest.fixture
def host(app_defaults):
    """ Returns a hostname to a running Elasticsearch host. """
    yield app_defaults


@pytest.fixture
def client(app_defaults, _client):
    yield _client


@pytest.fixture
def runner():
    yield CliRunner()


@pytest.fixture
def make_index(client):
    index_list = list()
    index_body = {
        'settings': {
            'index.number_of_shards': 1,
            'index.number_of_replicas': 1,
        }
    }

    def _factory(index=None):
        if index is None:
            index = 'some-index-{}'.format(len(index_list))
        index_list.append(index)
        r = client.indices.create(index, body=index_body)
        ok = r.get('acknowledged')
        assert ok
        return index

    yield _factory


@pytest.fixture
def empty_index(make_index):
    yield make_index()
