import logging
import sys

import click

from esok.constants import CONFIGURATION_ERROR

LOG = logging.getLogger(__name__)


@click.command()
@click.pass_obj
def config(obj):
    """Print current configuration."""
    conf = obj["user_config_file"]
    try:
        with open(conf, u"r") as f:
            content = f.read()
    except IOError:
        LOG.exception(u"Could not read the configuration file: {}".format(conf))
        sys.exit(CONFIGURATION_ERROR)

    click.echo(u"Configuration file location: {}".format(conf))
    click.echo(u"Contents:\n")
    click.echo(content)
