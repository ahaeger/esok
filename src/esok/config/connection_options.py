import functools
import logging
import sys
from ssl import create_default_context

import click
from elasticsearch import Elasticsearch
from urllib3.exceptions import HTTPError

from esok.constants import CLI_ERROR, CONFIGURATION_ERROR, USER_ERROR

LOG = logging.getLogger(__name__)
_CONNECTIONS_KEY = "{}.connections".format(__name__)


def connection_options(f):
    """Adds Elasticsearch connection options.

    This decorator is intended to be used on a click.Group, coupled with
    per_connection() on a sub-command.
    """
    f = click.option(
        "-t",
        "--timeout",
        type=click.INT,
        default=10,
        show_default=True,
        metavar="SECONDS",
        help="Timeout in seconds against Elasticsearch.",
    )(f)
    f = click.option(
        "-u",
        "--user",
        type=click.STRING,
        metavar="NAME",
        help="User for Elasticsearch basic auth. Prompts for password.",
    )(f)
    f = click.option(
        "-C",
        "--ca-certificate",
        type=click.Path(exists=True, dir_okay=False, readable=True),
        help="Use TLS with your self-signed CA certificate.",
    )(f)
    f = click.option(
        "-T",
        "--tls",
        type=click.BOOL,
        is_flag=True,
        help="Enable TLS against Elasticsearch.",
    )(f)
    f = click.option(
        "-s", "--sites", type=click.STRING, metavar="NAME", help="Sites to connect to."
    )(f)
    f = click.option(
        "-c",
        "--cluster",
        type=click.STRING,
        metavar="NAME",
        help="Cluster to connect to.",
    )(f)
    f = click.option(
        "-H",
        "--host",
        type=click.STRING,
        metavar="NAME",
        help="Specific host to connect to.",
    )(f)

    @functools.wraps(f)
    def decorator(
        sites, cluster, host, user, ca_certificate, tls, timeout, *args, **kwargs
    ):
        ctx = click.get_current_context()
        if user:
            password_option = click.prompt(
                f'Password for user "{user}"', hide_input=True
            )
        else:
            password_option = None

        ctx.meta[_CONNECTIONS_KEY] = dict(
            host_option=host,
            cluster_option=cluster,
            sites_option=sites,
            user_option=user,
            password_option=password_option,
            ca_certificate_option=ca_certificate,
            tls_option=tls,
            timeout_option=timeout,
        )
        return f(*args, **kwargs)

    return decorator


def per_connection(include_site=False):
    def wrapper(f):
        @functools.wraps(f)
        def decorator(*args, **kwargs):
            ctx = click.get_current_context().find_root()

            # A bit of an ugly dependency on the ctx.obj having to be set up
            # externally, with a dictionary structure that is assumed in this file.
            if (
                _CONNECTIONS_KEY not in ctx.meta
                or ctx.obj is None
                or "config" not in ctx.obj
            ):
                LOG.error(
                    "Connection options mismatch. This is a bug. "
                    "Would you please file a bug report? Thanks!"
                )
                sys.exit(CLI_ERROR)

            cli_options = ctx.meta[_CONNECTIONS_KEY]
            config = ctx.obj["config"]
            config.update(cli_options)
            clients = _create_clients(config)

            for client, site, cluster in clients:
                if len(clients) > 1:
                    click.secho(
                        "{} - {}:".format(cluster, site), bold=True, underline=True
                    )

                if include_site:
                    r = f(client, site, *args, **kwargs)
                else:
                    r = f(client, *args, **kwargs)

                ok = r is None
                if not ok:
                    # TODO (haeger) We never end up here
                    # Because f usually throws errors.
                    click.secho("FAIL", fg="red")
                    # TODO (haeger) Make it configurable if you want to continue or not?
                    break
                elif len(clients) > 1:
                    click.secho("OK", fg="green")

            # TODO (haeger) Should this aggregate and propagate return values somehow?
            return None

        return decorator

    return wrapper


def resolve_remote(remote, site):
    """Resolve remote's hostname, if exists.

    :param remote: Remote name given by user.
    :param site: Site given by @per_connection decorator.
    """
    config = click.get_current_context().obj["config"]
    if site is None and "{site}" in config["cluster_hostname_pattern"]:
        client = _make_client(remote)
    else:
        config = config.copy()
        config.update(
            host_option=None, cluster_option=remote, sites_option=site
        )
        client = _create_clients(config).pop()[0]
    return client


def _create_clients(config):
    """
    Resolve which clients to instantiate, based on the config file and passed flags.
    :param config The config dictionary
    :return: A list of Elasticsearch clients
    """
    host_option = config["host_option"]
    cluster_option = config["cluster_option"]
    sites_option = config["sites_option"]
    connections = config["connections"]
    default_connection = config["default_connection"]

    if host_option is not None:
        if cluster_option or sites_option:
            LOG.error("--host cannot be used with --cluster or --sites")
            sys.exit(USER_ERROR)

        client = _make_client(host_option, config)
        clients = [(client, None, None)]

    elif cluster_option in connections.keys():
        clients = _cluster_clients(connections, cluster_option, sites_option, config)

    elif cluster_option is not None:
        if config["cluster_hostname_pattern"] is None:
            LOG.error(
                "Neither cluster section or hostname pattern is defined for specified "
                "cluster. Cannot create connection. Check your config file."
            )
            sys.exit(USER_ERROR)

        clients = _patterned_hostname(config, cluster_option, sites_option)

    elif default_connection in connections.keys():
        # Default host is a defined cluster.
        clients = _cluster_clients(
            connections, default_connection, sites_option, config
        )

    else:
        # No connection info given, fallback to default host.
        if sites_option:
            LOG.error(
                "--sites specified, but default connection is not a "
                "predefined connection. Check your config file."
            )
            sys.exit(USER_ERROR)
        client = _make_client(default_connection, config)
        clients = [(client, None, None)]

    return clients


def _cluster_clients(connections, cluster_option, sites_option, config):
    sites = connections.get(cluster_option)
    clients = list()
    desired_sites = _cluster_sites(connections, sites_option, cluster_option)

    for site in desired_sites:
        hostname = sites.get(site)
        if hostname is None:
            LOG.error(
                'The cluster "{cluster}" has no defined site "{site}".\n'
                "Check your config file.".format(cluster=cluster_option, site=site)
            )
            sys.exit(USER_ERROR)

        client = _make_client(hostname, config)
        clients.append((client, site, cluster_option))

    return clients


def _cluster_sites(connections, sites_option, cluster_option):
    # Use specified sites if they are given,
    # otherwise fallback to all sites in config file
    return (
        _parse_sites(sites_option)
        if sites_option
        else connections[cluster_option].keys()
    )


def _patterned_hostname(config, cluster_option, sites_option):
    cluster_hostname_pattern = config["cluster_hostname_pattern"]
    default_sites = config["cluster_pattern_default_sites"]

    if "{cluster}" not in cluster_hostname_pattern:
        LOG.error(
            '"cluster_hostname_pattern" must contain the "{cluster}" variable. '
            "Check your config file."
        )
        sys.exit(CONFIGURATION_ERROR)

    if sites_option is not None:
        if "{site}" not in cluster_hostname_pattern:
            LOG.error(
                'Site option is specified, but "{site}" variable is missing in '
                '"cluster_hostname_pattern". Check your config file.'
            )
            sys.exit(USER_ERROR)

        sites = _parse_sites(sites_option)
    else:
        if "{site}" not in cluster_hostname_pattern and default_sites is not None:
            LOG.error(
                '"cluster_pattern_default_sites" are defined, but "{site}" variable is '
                'missing in "cluster_hostname_pattern". Check your config file.'
            )
            sys.exit(CONFIGURATION_ERROR)

        sites = _parse_sites(default_sites)

    clients = list()
    try:
        if sites is not None:
            for site in sites:
                client = _make_client(
                    cluster_hostname_pattern.format(cluster=cluster_option, site=site),
                    config,
                )
                clients.append((client, site, cluster_option))
        else:
            client = _make_client(
                cluster_hostname_pattern.format(cluster=cluster_option), config
            )
            clients.append((client, None, cluster_option))

    except KeyError:
        LOG.exception(
            "Could not parse cluster hostname pattern. Pattern must include "
            '"{cluster}" variable, for usage with --cluster option. '
            'Optionally, "{site}" can also be defined for use with either --sites '
            'or "cluster_pattern_default_sites" configuration.'
        )
        sys.exit(USER_ERROR)

    return clients


def _parse_sites(sites):
    return [site.strip() for site in sites.split(",")] if sites is not None else None


def _make_client(hostname, config):
    ssl_context = create_default_context(cafile=config["ca_certificate_option"])
    user = config["user_option"]
    password = config["password_option"]
    if user is not None:
        http_auth = (user, password)
    else:
        http_auth = None

    try:
        return Elasticsearch(
            hosts=[hostname],
            timeout=config["timeout_option"],
            http_auth=http_auth,
            use_ssl=config["tls_option"] or config["ca_certificate_option"] is not None,
            ssl_context=ssl_context,
        )
    except HTTPError:
        LOG.exception(
            "Could not create Elasticsearch client for given hostname: {}".format(
                hostname
            )
        )
        sys.exit(USER_ERROR)
