import json
import logging
import sys

import click
from click_didyoumean import DYMGroup
from elasticsearch import NotFoundError, TransportError

from esok.config.connection_options import per_connection, resolve_remote
from esok.constants import UNKNOWN_ERROR, USER_ERROR
from esok.util import clean_index

LOG = logging.getLogger(__name__)


@click.group(cls=DYMGroup)
def reindex():
    """Reindex operations."""
    pass


@reindex.command()
@click.argument("source_index", type=click.STRING)
@click.argument("target_index", type=click.STRING)
@click.option(
    "-R",
    "--remote",
    type=click.STRING,
    metavar="NAME",
    help="Remote cluster or hostname as reindex source.",
)
@click.option(
    "-S",
    "--socket-timeout",
    type=click.STRING,
    default="30s",
    help="Socket timeout for remote host.",
    show_default=True,
)
@click.option(
    "-C",
    "--connection-timeout",
    type=click.STRING,
    default="30s",
    show_default=True,
    help="Connection timeout for remote host.",
)
@click.option(
    "-w",
    "--wait",
    is_flag=True,
    help="Wait for reindexing to finish, before returning.",
)
@click.option(
    "-s",
    "--size",
    type=click.INT,
    default=None,
    help="Upper boundary for count of docs to reindex.",
    show_default=True,
)
@click.option(
    "-b",
    "--batch-size",
    type=click.INT,
    default=None,
    help="The batch size to use while indexing.",
    show_default=True,
)
@click.option(
    "-i",
    "--slices",
    type=click.INT,
    default=0,
    show_default=True,
    help='Count of slices to use. "auto" slicing is the default, but slicing >1 only works when reindexing'
    "indices on the same cluster. If reindexing from remote (using -R) slices will be set to 1.",
)
@per_connection(include_site=True)
def start(
    client,
    site,
    source_index,
    target_index,
    remote,
    wait,
    size,
    socket_timeout,
    connection_timeout,
    batch_size,
    slices,
):
    """Start a reindex task.

    Use the regular connection options to reindex between indices on the same cluster.

    \b
    $ esok -c target-cluster reindex start source-index target-index

    Use the -R (--remote) option to reindex from a remote cluster. The remote cluster hostname is resolved in the same
    manner as the --cluster option.

    \b
    $ esok -c target-cluster reindex start -R source-cluster source-index target-index
    $ esok -c target-cluster reindex start -R source-host.example.com source-index target-index
    $ esok -H target-host.example.com reindex start -R source-host.example.com source-index target-index

    """
    # Resolve which hostname and clients to use
    if remote is not None:
        source_client = resolve_remote(remote, site)
    else:
        source_client = client

    # Check if source index exists
    try:
        source = source_client.indices.get(index=source_index)
    except TransportError as e:
        if e.status_code == 404:
            LOG.error('Source index "%s" does not exist.', source_index)
            exit(USER_ERROR)

        LOG.error("Error occurred when checking for source index.")
        raise

    # Check if destination index exists
    try:
        destination = client.indices.get(index=target_index)
    except TransportError as e:
        if e.status_code != 404:
            LOG.error("Error occurred when checking for destination index.")
            raise
        LOG.info("Destination index does not exist.")
        destination = None

    if destination is None:
        # Need to create the destination mapping
        click.confirm(
            "Destination index does not exist and will therefore be created from the "
            "source's mapping.\nDo you want to continue?",
            default=True,
            abort=True,
        )

        cleaned_index = clean_index(source, False, False)

        r = client.indices.create(index=target_index, body=cleaned_index)
        ok = r.get("acknowledged")
        LOG.debug(json.dumps(r))
        if not ok:
            sys.exit(UNKNOWN_ERROR)

        LOG.info("Index created: %s", target_index)

    if remote is not None:
        source = {
            "remote": {
                "host": source_client.transport.get_connection().host,
                "socket_timeout": socket_timeout,
                "connect_timeout": connection_timeout
                # TODO Add username and password options?
            },
            "index": source_index,
        }

        # Reindex from remote only supports slices == 1
        if slices != 1:
            slices = 1
            LOG.info("Slicing set to %s because reindexing from remote.", slices)

    else:
        source = dict(index=source_index)

    if batch_size is not None:
        source["size"] = batch_size

    body = {"source": source, "dest": {"index": target_index}}

    slices = "auto" if slices == 0 else slices
    if size:
        body["size"] = size

    r = client.reindex(body, wait_for_completion=wait, slices=slices)
    if wait:
        click.echo(json.dumps(r))
    else:
        taskId = r.get("task")
        click.echo("Task ID: {}".format(taskId))


@reindex.command(name="list")
@per_connection()
def list_reindex_tasks(client):
    """List currently running reindexing task IDs."""
    r = client.tasks.list(actions="*reindex", detailed=True)
    LOG.debug(json.dumps(r))
    for node_id, node_data in r.get("nodes").items():
        for task_id in node_data.get("tasks").keys():
            click.echo(task_id)


@reindex.command()
@click.argument("task_id", type=click.STRING)
@per_connection()
def cancel(client, task_id):
    """Cancel a given reindex task.

    Use the list command to see currently running tasks.

    """
    # ES does not throw an error if the task doesn't exist.
    client.tasks.cancel(task_id=task_id)


@reindex.command()
@click.argument("task_id", type=click.STRING)
@per_connection()
def progress(client, task_id):
    """Print the progress of a given reindex task."""
    try:
        task_info = client.tasks.get(task_id=task_id)
    except NotFoundError:
        click.echo("Task with id {} not found!".format(task_id))
        sys.exit(USER_ERROR)

    reindex_status = task_info["task"]["status"]
    LOG.debug(json.dumps(reindex_status))
    modified = (
        reindex_status["created"]
        + reindex_status["updated"]
        + reindex_status["deleted"]
    )

    total = reindex_status["total"]
    click.echo("{:.1f}%".format((float(modified) / total) * 100))
