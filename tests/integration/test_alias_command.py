import pytest
from elasticsearch import TransportError

from esok.esok import esok


def test_list(runner, empty_index, make_alias):
    alias = make_alias(empty_index)
    r = runner.invoke(esok, ['alias', 'list'])
    assert r.exit_code == 0
    assert empty_index in r.output
    assert alias in r.output


def test_create(runner, client, empty_index):
    alias = 'some-alias'
    r = runner.invoke(esok, ['alias', 'create', alias, empty_index])
    assert r.exit_code == 0
    assert '{} {}'.format(alias, empty_index) in client.cat.aliases()


def test_create_with_missing_index(runner, client):
    r = runner.invoke(esok, ['alias', 'create', 'some-alias', 'some-index'])
    assert isinstance(r.exception, TransportError)


def test_delete(runner, client, make_index, make_alias):
    some_index = make_index()
    other_index = make_index()
    alias = make_alias(some_index)
    make_alias(other_index, alias)

    r = runner.invoke(esok, ['alias', 'delete', alias, some_index])
    assert r.exit_code == 0

    aliases = client.cat.aliases()
    assert some_index not in aliases
    assert '{} {}'.format(alias, other_index) in aliases


def test_delete_with_missing_index(runner, client, empty_index, make_alias):
    alias = make_alias(empty_index)
    r = runner.invoke(esok, ['alias', 'delete', alias, 'other-index'])
    assert isinstance(r.exception, TransportError)


def test_swap(runner, client, make_index, make_alias):
    some_index = make_index()
    other_index = make_index()
    alias = make_alias(some_index)

    r = runner.invoke(esok, ['alias', 'swap', alias, some_index, other_index])
    assert r.exit_code == 0

    aliases = client.cat.aliases()
    assert some_index not in aliases
    assert '{} {}'.format(alias, other_index) in aliases


def test_swap_with_missing_to_index(runner, client, empty_index, make_alias):
    alias = make_alias(empty_index)

    r = runner.invoke(esok, ['alias', 'swap', alias, empty_index, 'missing-index'])
    assert isinstance(r.exception, TransportError)
    assert '{} {}'.format(alias, empty_index) in client.cat.aliases()


def test_swap_with_missing_from_index(runner, client, empty_index):
    r = runner.invoke(esok, ['alias', 'swap', 'some-alias', 'missing-index', empty_index])
    assert isinstance(r.exception, TransportError)
    assert '' == client.cat.aliases()


@pytest.fixture
def make_alias(client):
    alias_list = list()

    def _factory(index, alias=None):
        if alias is None:
            alias = 'some-alias-{}'.format(len(alias_list))
        alias_list.append(alias)
        client.indices.put_alias(index, alias)
        return alias

    yield _factory
