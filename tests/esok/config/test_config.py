import logging

from esok.config.config import read_config_files
from esok.constants import DEFAULT_CONFIG


def test_config_defaults(user_config_file, caplog):
    with caplog.at_level(logging.WARNING):
        config = read_config_files(str(user_config_file), DEFAULT_CONFIG)

    assert config['default_connection'] == 'localhost'
    assert config['cluster_hostname_pattern'] is None
    assert config['cluster_pattern_default_sites'] is None
    assert 'connections' in config

    assert str(user_config_file) in caplog.text


def test_config_with_cluster_section(user_config_file, test_app_dir):
    user_config_file.write_text("""
    [cluster:dummy-cluster]
    site1 = data.example.com
    site2 = logs.example.com
    site3 = backup.example.com
    """)

    config = read_config_files(str(user_config_file), DEFAULT_CONFIG)

    assert 'default_connection' in config, 'Defaults should be used'
    assert 'cluster_hostname_pattern' in config, 'Defaults should be used'
    assert 'cluster_pattern_default_sites' in config, 'Defaults should be used'

    cluster = config['connections'].get('dummy-cluster')
    assert cluster is not None, 'Cluster definition should be included'
    assert cluster.get('site1') == 'data.example.com', 'Cluster/site definition should be included'
    assert cluster.get('site2') == 'logs.example.com', 'Cluster/site definition should be included'
    assert cluster.get('site3') == 'backup.example.com', 'Cluster/site definition should be included'
