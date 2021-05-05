import logging
from configparser import ConfigParser

LOG = logging.getLogger(__name__)


def read_config_files(user_config_path, default_config_path):
    configParser = ConfigParser()

    # TODO (haeger) More sophisticated error checking and handling.
    paths = configParser.read([default_config_path, user_config_path])
    if user_config_path not in paths:
        LOG.warning('Could not read user\'s config file at: {}'.format(user_config_path))

    config = dict()
    config['default_connection'] = configParser.get('general', 'default_connection')
    cluster_hostname_pattern = configParser.get('general', 'cluster_hostname_pattern')
    config['cluster_hostname_pattern'] = cluster_hostname_pattern if cluster_hostname_pattern != '' else None
    cluster_pattern_default_sites = configParser.get('general', 'cluster_pattern_default_sites')
    if cluster_pattern_default_sites != '':
        config['cluster_pattern_default_sites'] = cluster_pattern_default_sites
    else:
        config['cluster_pattern_default_sites'] = None

    # Create a mapping between cluster and sites
    cluster_sections = [section for section in configParser.sections() if section.startswith('cluster:')]
    connections = {section[8:]: dict(configParser[section]) for section in cluster_sections}
    config['connections'] = connections

    return config
