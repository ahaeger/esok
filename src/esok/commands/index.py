import json
import logging
import sys

import click
from click_didyoumean import DYMGroup
from elasticsearch import Elasticsearch, TransportError
from elasticsearch.helpers import bulk, scan

from esok.config.connection_options import per_connection, resolve_remote
from esok.constants import UNKNOWN_ERROR, USER_ERROR
from esok.util import clean_index

LOG = logging.getLogger(__name__)


@click.group(cls=DYMGroup)
def index():
    """Index operations."""
    pass


@index.command(name="list")
@per_connection()
def list_indices(client):
    """List existing indices."""
    # TODO (haeger) Sort on index name? Make it an option?
    r = client.cat.indices(v=True)
    click.echo(r)


@index.command()
@click.argument("name", type=click.STRING)
@per_connection()
def touch(client, name):
    """Create an index without mapping."""
    r = client.indices.create(index=name)
    LOG.info(json.dumps(r))
    ok = r.get("acknowledged")
    if not ok:
        sys.exit(UNKNOWN_ERROR)


@index.command()
@click.argument("name", type=click.STRING)
@click.argument("mapping", type=click.Path(exists=True, dir_okay=False, readable=True))
@per_connection()
def create(client, name, mapping):
    """Create a new index from given mapping."""
    with open(mapping, "r") as f:
        mapping_json = json.load(f)
    r = client.indices.create(index=name, body=mapping_json)
    ok = r.get("acknowledged")
    LOG.info(json.dumps(r))
    if not ok:
        sys.exit(UNKNOWN_ERROR)


@index.command()
@click.argument("source_index", type=click.STRING)
@click.argument("new_index", type=click.STRING)
@click.option(
    "-R",
    "--remote",
    type=click.STRING,
    metavar="HOSTNAME",
    help="Remote cluster or hostname to copy from. If no cluster with the "
    "given name is configured, the passed value will be used as the "
    "hostname directly.",
)
@click.option(
    "-m",
    "--skip-mapping",
    is_flag=True,
    help="Skip the mapping part of the index when copying.",
)
@click.option(
    "-s",
    "--skip-settings",
    is_flag=True,
    help="Skip the settings part of the index when copying.",
)
@per_connection(include_site=True)
def copy(client, site, source_index, new_index, remote, skip_mapping, skip_settings):
    """Copy an existing index's mapping and setting to a new index.

    This will not copy the data of the index - use the reindex command for that.
    """
    # Resolve which source client to use
    if remote is not None:
        source_client = resolve_remote(remote, site)
    else:
        source_client = client

    # Fetch source index, if exists
    try:
        source_mapping = source_client.indices.get(index=source_index)
    except TransportError as e:
        LOG.error("Error occurred when checking for source index.")
        if e.status_code == 404:
            LOG.error("The source index does not exist.")
            exit(USER_ERROR)
        raise

    cleaned_mapping = clean_index(source_mapping, skip_settings, skip_mapping)

    r = client.indices.create(index=new_index, body=cleaned_mapping)
    ack = r.get("acknowledged")
    LOG.info(json.dumps(r))
    if not ack:
        LOG.warning(
            "Request timed out before acknowledge was received. "
            "Index might not have been created yet."
        )


@index.command()
@click.argument("name", type=click.STRING)
@per_connection()
def delete(client: Elasticsearch, name):
    """Delete an index."""
    # TODO (haeger) Should prompt confirmation if there is an alias on the index
    if name in ["_all", "*"]:
        click.confirm("Really delete ALL indices on the cluster?", abort=True)

    r = client.indices.delete(index=name)
    LOG.info(json.dumps(r))
    ok = r.get("acknowledged")
    if not ok:
        sys.exit(UNKNOWN_ERROR)


@index.command()
@click.argument("name", type=click.STRING)
@per_connection()
def get(client, name):
    """Get index details."""
    r = client.indices.get(index=name)
    click.echo(json.dumps(r))


@index.command()
@click.argument("name", type=click.STRING)
@per_connection()
def stats(client, name):
    """Fetch index statistics."""
    r = client.indices.stats(index=name)
    click.echo(json.dumps(r))
    ok = "_all" in r.keys()
    if not ok:
        sys.exit(UNKNOWN_ERROR)


@index.command()
@click.argument("name", type=click.STRING)
@click.argument("shard_count", type=click.INT)
@click.option(
    "-a",
    "--absolute",
    is_flag=True,
    help="Indicates that the given number of shards is an absolute replica count.",
)
@click.option(
    "-n", "--nodes", type=click.INT, help="Manually set node count of the cluster."
)
@per_connection()
def shards(client, name, shard_count, absolute, nodes):
    """Set the number of shards per machine."""
    # TODO (haeger) Need to check if shard allocation and rebalancing is enabled
    if absolute:
        replica_count = shard_count
        LOG.info("Using manually set replica count: {}".format(shard_count))

    else:
        if not nodes:
            # Fetch node count.
            r = client.nodes.stats(
                metric="process"
            )  # Using this metric because payload is small
            cluster_node_count = r.get("nodes").values()
            # Figure out how many data nodes there are in this cluster
            data_node_count = sum(
                1 for item in cluster_node_count if "data" in item.get("roles")
            )
            LOG.debug(
                "Resolved data node count from cluster: {}".format(data_node_count)
            )
        else:
            LOG.debug("Using manually set node count: {}".format(nodes))
            data_node_count = nodes

        # Fetch number of primary shards for this index.
        r = client.indices.get(index=name)
        primary_count = int(
            r.get(name).get("settings").get("index").get("number_of_shards")
        )
        LOG.debug("Primary shard count: {}".format(primary_count))
        LOG.debug("Desired shard count per host: {}".format(shard_count))
        # Calculate the appropriate number of replicas
        replica_count = (shard_count * data_node_count - primary_count) / primary_count
        replica_count = max(
            replica_count, 0.0
        )  # For the edge case where replica_count == -1

        if not replica_count.is_integer():
            click.echo(
                "The cluster configuration and desired shards per machine "
                "resulted in {} total replicas.\n"
                "This will be rounded to {} replicas in total.".format(
                    replica_count, int(replica_count)
                )
            )

            if not click.confirm("Do you want to continue?"):
                sys.exit()

        LOG.info("Calculated replica count: {}".format(replica_count))

    body = {"index": {"number_of_replicas": int(replica_count)}}
    r = client.indices.put_settings(body, index=name)

    ok = r.get("acknowledged")
    LOG.info(json.dumps(r))

    if not ok:
        sys.exit(UNKNOWN_ERROR)


@index.command()
@click.argument("name", type=click.STRING)
@click.option(
    "-o",
    "--output-file",
    type=click.File("w"),
    default="-",
    show_default=True,
    help="Specify file to output to.",
)
@click.option(
    "-c",
    "--chunk-size",
    type=click.INT,
    default=1000,
    show_default=True,
    help="Number of documents (per shard) to fetch in each individual request.",
)
@click.option(
    "-s",
    "--scroll-time",
    type=click.STRING,
    default="5m",
    show_default=True,
    help="The duration the cluster shall maintain a consistent view.",
)
@per_connection()
def read(client, name, output_file, chunk_size, scroll_time):
    """Dump index contents to stdout or file.

    Note: subsequent reads from several cluster will overwrite contents in output file.

    Examples:

    \b
    $ esok index read index-name
    $ esok index read -o output.json index-name
    $ esok index read index-name | jq -c '{_id, _source}' > output.json
    """
    r = scan(client, index=name, size=chunk_size, scroll=scroll_time)
    for doc in r:
        click.echo(json.dumps(doc), output_file)


@index.command()
@per_connection()
@click.argument("docs", type=click.Path(allow_dash=True))
@click.option(
    "-i",
    "--index-name",
    type=click.STRING,
    help="Forces target index to given name for all documents.",
)
@click.option(
    "-c",
    "--chunk-size",
    type=click.INT,
    help="Number of docs in one chunk",
    default=500,
    show_default=True,
)
@click.option("--refresh", is_flag=True, help="Refresh the index after indexing.")
@click.option(
    "-C",
    "--max-chunk-bytes",
    type=click.INT,
    help="The maximum size of the request in bytes",
    default=int(100e6),
    show_default=True,
)
@click.option(
    "-R",
    "--max-retries",
    type=click.INT,
    help="Maximum number of times a document will be retried when 429 is received",
    default=0,
    show_default=True,
)
@click.option(
    "-b",
    "--initial-backoff",
    type=click.INT,
    help="Number of seconds to wait before the first retry. Any subsequent "
    "retries will be powers of initial-backoff * 2^retry_number",
    default=2,
    show_default=True,
)
@click.option(
    "-B",
    "--max-backoff",
    type=click.INT,
    help="Maximum number of seconds a retry will wait",
    default=600,
    show_default=True,
)
def write(
    client,
    docs,
    index_name,
    refresh,
    chunk_size,
    max_chunk_bytes,
    max_retries,
    initial_backoff,
    max_backoff,
):
    """ Write to a given index.

    The input file is expected to be in the "JSON-lines" format, i.e. with one valid
    JSON-object per row. Pass - to read from stdin.

    Reserved keys include '_index', '_type', '_id' and '_source' (among others), which
    are all optional. If '_source' is present Elasticsearch will assume that the
    document to index resides within it. If '_source' is not present, all other
    non-reserved keys will be indexed.

    For more details, see:

    \b
    http://elasticsearch-py.readthedocs.io/en/5.5.1/helpers.html#bulk-helpers

    Examples:

    \b
    $ esok index write -i index-name ./data.json
    $ echo '{"hello": "world"}' | esok index write -i index-name -
    $ esok index read index-name | jq -c '{_id, stuff: ._source.title}' \\
         | esok index write -i index-name-1 -
    """
    for actions in _read_actions(docs, max_chunk_bytes):
        for action in actions:
            if index_name is not None:
                action["_index"] = index_name

            action["_type"] = (
                "_doc" if "_type" not in action.keys() else action["_type"]
            )

        successful_request_count, errors = bulk(
            client,
            actions,
            chunk_size=chunk_size,
            raise_on_error=False,
            max_chunk_bytes=max_chunk_bytes,
            max_retries=max_retries,
            initial_backoff=initial_backoff,
            max_backoff=max_backoff,
            refresh=refresh,
        )

        chunk_count = len(actions)
        ok = successful_request_count == chunk_count

        # TODO (haeger) How to handle 429s, when Elasticsearch is only pushing back?
        # That scenario would just fail right now.
        if not ok:
            LOG.error(
                "{} / {} failed documents.".format(
                    chunk_count - successful_request_count, chunk_count
                )
            )
            for error in errors:
                LOG.error(json.dumps(error))

            sys.exit(UNKNOWN_ERROR)


def _read_actions(path, max_chunk_bytes):
    def _stripped_lines():
        return [
            json.loads(s.strip())
            for s in f.readlines(max_chunk_bytes)
            if s.strip() != ""
        ]

    with click.open_file(path, "r", "UTF-8") as f:
        chunk = _stripped_lines()
        if not chunk:
            LOG.warning("No actions were read. Is the file empty?")

        while chunk:
            yield chunk
            chunk = _stripped_lines()
