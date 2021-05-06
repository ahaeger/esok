import logging.config
import shutil
from os import makedirs, path

import click
import yaml

from esok.constants import APP_CONFIG_BASENAME, DEFAULT_CONFIG

LOG = logging.getLogger(__name__)


def app_init(app_dir, log_dir_name="logs"):
    """
    Initialize app directories and configurations.

    :param app_dir: File path to the app's directory
    :param log_dir_name: Name of the subdirectory of ``app_dir``
           in which logs should be placed
    """
    _init_dirs(app_dir, log_dir_name)
    _init_logging(path.join(app_dir, log_dir_name))
    _copy_default_app_config(app_dir)


def _init_dirs(app_dir, log_dir_name):
    # deep_paths should span all leaf directories required for the app to work
    deep_paths = [log_dir_name]
    deep_paths = [path.join(app_dir, dir_name) for dir_name in deep_paths]
    try:
        for deep_path in deep_paths:
            if not path.exists(deep_path):
                makedirs(deep_path)  # Recursively creates directories
    except (OSError, IOError):
        click.secho(
            u"Could not setup application directory: {}".format(app_dir),
            err=True,
            fg=u"red",
        )


def _init_logging(log_dir):
    """
    Load logging configuration.

    :param app_dir: File path to the app's directory
    :param log_dir_name: Name of the subdirectory of ``app_dir``
           in which logs should be placed
    """
    this_file = path.dirname(path.abspath(__file__))
    with open(path.join(this_file, u"resources", u"logging.yaml"), u"r") as f:
        logging_config = yaml.safe_load(f)

    # Update file handlers to output to the correct logging folder
    handler_filename_key = u"filename"
    for handler in logging_config.get(u"handlers").values():
        if handler.get(handler_filename_key):
            full_log_path = path.join(log_dir, handler.get(handler_filename_key))
            handler[handler_filename_key] = full_log_path

    try:
        logging.config.dictConfig(logging_config)
    except ValueError:
        click.secho(u"Could not setup logging configuration.", err=True, fg=u"red")


def _copy_default_app_config(
    app_dir, config_basename=None, default_config=DEFAULT_CONFIG
):
    """Places the default configuration file in the user's app directory."""
    if config_basename is None:
        config_basename = APP_CONFIG_BASENAME

    if not path.isfile(path.join(app_dir, config_basename)):
        try:
            shutil.copy(default_config, app_dir)

        except (OSError, IOError, shutil.Error):
            click.secho(
                u"Could not write default config to: {}".format(app_dir),
                err=True,
                fg=u"red",
            )
