import json
import logging
import sys

import click
from click_didyoumean import DYMGroup

from esok.config.connection_options import per_connection
from esok.constants import UNKNOWN_ERROR

LOG = logging.getLogger(__name__)


@click.group(cls=DYMGroup)
def alias():
    """ Alias operations. """
    pass


@alias.command(name='list')
@per_connection()
def list_aliases(client):
    """ List existing index aliases. """
    # TODO (haeger) Sort on index name? Make it an option?
    r = client.cat.aliases(v=True)
    click.echo(r)


@alias.command()
@click.argument('name', type=click.STRING)
@click.argument('index', type=click.STRING)
@per_connection()
def create(client, name, index):
    """ Create an alias for an index. """
    r = client.indices.put_alias(index=index, name=name)
    LOG.info(json.dumps(r))
    ok = r.get('acknowledged')
    if not ok:
        sys.exit(UNKNOWN_ERROR)


@alias.command()
@click.argument('name', type=click.STRING)
@click.argument('index', type=click.STRING)
@per_connection()
def delete(client, name, index):
    """ Delete alias from index. """
    r = client.indices.delete_alias(name=name, index=index)
    ok = r.get('acknowledged')
    LOG.info(json.dumps(r))
    if not ok:
        sys.exit(UNKNOWN_ERROR)


@alias.command()
@click.argument('name', type=click.STRING)
@click.argument('from_index', type=click.STRING)
@click.argument('to_index', type=click.STRING)
@per_connection()
def swap(client, name, from_index, to_index):
    """ Swap alias between indices, atomically. """
    r = client.indices.update_aliases({
        'actions': [
            {'add': {'index': to_index, 'alias': name}},
            {'remove': {'index': from_index, 'alias': name}}
        ]
    })
    ok = r.get('acknowledged')
    LOG.info(json.dumps(r))
    if not ok:
        sys.exit(UNKNOWN_ERROR)
