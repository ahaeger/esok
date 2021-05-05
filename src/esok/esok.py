import logging
import sys
from json import JSONDecodeError
from os import path

import click
from click_didyoumean import DYMGroup
from elasticsearch import TransportError

from esok.commands.alias import alias
from esok.commands.config import config as config_command
from esok.commands.index import index
from esok.commands.reindex import reindex
from esok.config.config import read_config_files
from esok.config.connection_options import connection_options
from esok.constants import APP_CONFIG_BASENAME, APP_NAME, CLUSTER_ERROR, DEFAULT_CONFIG, UNKNOWN_ERROR, USER_ERROR
from esok.init import app_init
from esok.log.decorator import critical, debug, error, exception, silence, verbose, verbosity

LOG = logging.getLogger(__name__)

CONTEXT_SETTINGS = dict(help_option_names=[u'-h', u'--help'])


def app_dir_callback(ctx, param, value):
    if value is None:
        value = click.get_app_dir(APP_NAME, force_posix=True)
    app_init(value)
    return value


@click.group(context_settings=CONTEXT_SETTINGS, cls=DYMGroup, invoke_without_command=True)
@click.option('-a', '--app-dir', show_default=True, callback=app_dir_callback, is_eager=True,
              type=click.Path(exists=True, dir_okay=True, readable=True, writable=True, allow_dash=False),
              help='Directory in which esok will setup configuration files and write logs to.')
@connection_options
@verbosity(__package__, default=u'WARNING')
@click.option(u'-v', u'--verbose', is_flag=True, expose_value=False,
              callback=verbose, help=u'Include INFO logs to stdout. Same as --info.')
@click.option(u'--info', is_flag=True, expose_value=False,
              callback=verbose, help=u'Include INFO logs to stdout. Same as -v.')
@click.option(u'--debug', is_flag=True, expose_value=False,
              callback=debug, help=u'Include DEBUG logs to stdout.')
@click.option(u'--error', is_flag=True, expose_value=False,
              callback=error, help=u'Limit console output to ERROR logs or higher.')
@click.option(u'--exception', is_flag=True, expose_value=False,
              callback=exception, help=u'Limit console output to ERROR logs or higher. Also print stack traces.')
@click.option(u'--critical', is_flag=True, expose_value=False,
              callback=critical, help=u'Limit console output to CRITICAL logs or higher.')
@click.option(u'--silence', is_flag=True, expose_value=False,
              callback=silence, help=u'I\'ll shut up.')
@click.pass_context
def esok(ctx, app_dir):
    """ A CLI for Elasticsearch.

    Configure your Elasticsearch connections in the config file.
    View it by running: esok config

    Examples:

        \b
        $ esok config
        $ esok -H es.example.com index list
        $ esok -c my-cluster index create prod-v2 ~/mappings/prod.json
        $ esok -c my-cluster -s ew,ae alias swap prod prod-v1 prod-v2
    """
    LOG.debug('Using app directory: %s', app_dir)
    user_config_file = path.join(app_dir, APP_CONFIG_BASENAME)
    config = read_config_files(user_config_file, DEFAULT_CONFIG)
    ctx.ensure_object(dict)
    ctx.obj.update(dict(config=config, user_config_file=user_config_file))

    # This group-command is invoked even without supplying sub-commands, in order to set up the app directory.
    # But we still want to present help text if no sub-commands are provided.
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


def entry_point():
    try:
        return esok()

    except TransportError as e:
        LOG.exception('Transport Error')

        status = click.style(f'[{e.status_code}]', fg='red', bold=True)
        error_msg = e.error.replace('_', ' ').capitalize()
        LOG.error(f'{status} {error_msg}')

        if e.status_code != 'N/A' and isinstance(e.info, dict):
            reason = e.info.get('error', dict()).get('reason')
        else:
            reason = None

        if reason is not None:
            LOG.error(reason)

        status_code_family = str(e.status_code)[0]
        if status_code_family == '4':
            sys.exit(USER_ERROR)
        elif status_code_family == '5':
            sys.exit(CLUSTER_ERROR)
        else:
            sys.exit(UNKNOWN_ERROR)

    except FileNotFoundError as e:
        LOG.exception('File could not be found: {}'.format(e.filename))
        sys.exit(USER_ERROR)

    except JSONDecodeError as e:
        LOG.exception('Could not decode JSON document:\n%s', e.doc)
        sys.exit(USER_ERROR)

    except Exception:
        LOG.exception('Something got borked. Check the logs.')
        sys.exit(UNKNOWN_ERROR)

    finally:
        logging.shutdown()


esok.add_command(alias)
esok.add_command(index)
esok.add_command(config_command)
esok.add_command(reindex)
