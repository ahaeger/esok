import click
import pytest

from esok.config.connection_options import per_connection
from esok.constants import CLI_ERROR, CONFIGURATION_ERROR, USER_ERROR
from esok.esok import esok


@pytest.mark.usefixtures("mock_clients")
def test_no_connection_options(runner):
    clients, command = _attach_sub_command(esok)

    r = runner.invoke(esok, [command])

    assert r.exit_code == 0, "The command should succeed."
    assert clients == [
        "localhost"
    ], "Default connection should be used when no connection options are passed."


@pytest.mark.usefixtures("mock_clients")
def test_no_connection_options_and_sites_option(runner):
    clients, command = _attach_sub_command(esok)

    r = runner.invoke(esok, ["-s", "eu", command])

    assert r.exit_code == USER_ERROR, "Exit code should signal a user error."
    assert "Error" in r.output


@pytest.mark.usefixtures("mock_clients")
def test_host_option(runner):
    clients, command = _attach_sub_command(esok)

    expected_host = "some_host"
    r = runner.invoke(esok, ["-H", expected_host, command])

    assert r.exit_code == 0, "The command should succeed."
    assert clients == [expected_host], "Provided hostname should be used."


@pytest.mark.usefixtures("mock_clients")
def test_host_option_cannot_be_used_with_cluster(runner):
    clients, command = _attach_sub_command(esok)

    r = runner.invoke(esok, ["-H", "some_host", "-c", "some_cluster", command])

    assert r.exit_code == USER_ERROR, "Exit code should signal a user error."
    assert "Error" in r.output, "There should be error output explaining the issue."


@pytest.mark.usefixtures("mock_clients")
def test_host_option_cannot_be_used_with_sites(runner):
    clients, command = _attach_sub_command(esok)

    r = runner.invoke(esok, ["-H", "some_host", "-s", "site1,site2", command])

    assert r.exit_code == USER_ERROR, "Exit code should signal a user error."
    assert "Error" in r.output, "There should be error output explaining the issue."


@pytest.mark.usefixtures("mock_clients")
def test_cluster_with_missing_connection(runner):
    clients, command = _attach_sub_command(esok)

    r = runner.invoke(esok, ["-c", "some_cluster", command])

    assert r.exit_code == USER_ERROR, "Exit code should signal a user error."
    assert "Error" in r.output, "There should be error output explaining the issue."


@pytest.mark.usefixtures("mock_clients")
def test_cluster_with_predefined_connections(user_config_file, runner):
    user_config_file.write_text(
        """
    [cluster:awesome-cluster]
    eu = 192.168.0.1
    us = some.es.cluster.example.com
    ae = east-asia-host
    """
    )
    clients, command = _attach_sub_command(esok)

    r = runner.invoke(esok, ["-c", "awesome-cluster", command])

    assert r.exit_code == 0, "The command should succeed."
    assert "192.168.0.1" in clients, "Configured cluster should be part of the clients."
    assert (
        "some.es.cluster.example.com" in clients
    ), "Configured cluster should be part of the clients to connect to."
    assert (
        "east-asia-host" in clients
    ), "Configured cluster should be part of the clients to connect to."


@pytest.mark.usefixtures("mock_clients")
def test_cluster_with_predefined_connections_and_site_option(user_config_file, runner):
    user_config_file.write_text(
        """
    [cluster:awesome-cluster]
    eu = 192.168.0.1
    us = some.es.cluster.example.com
    ap = asia-host
    """
    )
    clients, command = _attach_sub_command(esok)

    r = runner.invoke(esok, ["-c", "awesome-cluster", "-s", "eu", command])

    assert r.exit_code == 0, "The command should succeed."
    assert ["192.168.0.1"] == clients, "Specified cluster should be the only client."


@pytest.mark.usefixtures("mock_clients")
def test_cluster_with_predefined_connections_and_missing_site_option(
    user_config_file, runner
):
    user_config_file.write_text(
        """
    [cluster:awesome-cluster]
    us = some.es.cluster.example.com
    ap = asia-host
    """
    )
    clients, command = _attach_sub_command(esok)

    r = runner.invoke(esok, ["-c", "awesome-cluster", "-s", "eu", command])

    assert r.exit_code == USER_ERROR, "Exit code should signal a user error."
    assert "Error" in r.output, "There should be error output explaining the issue."


@pytest.mark.usefixtures("mock_clients")
def test_cluster_with_invalid_pattern_config(user_config_file, runner):
    user_config_file.write_text(
        """
    [general]
    cluster_hostname_pattern = my-cluster
    """
    )
    clients, command = _attach_sub_command(esok)

    r = runner.invoke(esok, ["-c", "favorite", command])

    assert (
        r.exit_code == CONFIGURATION_ERROR
    ), "Exit code should signal a configuration error."
    assert "Error" in r.output


@pytest.mark.usefixtures("mock_clients")
def test_cluster_with_pattern_config_without_site(user_config_file, runner):
    user_config_file.write_text(
        """
    [general]
    cluster_hostname_pattern = my-{cluster}-cluster
    """
    )
    clients, command = _attach_sub_command(esok)

    r = runner.invoke(esok, ["-c", "favorite", command])

    assert r.exit_code == 0, "The command should succeed."
    assert (
        "my-favorite-cluster" in clients
    ), "Specified cluster should be the only client."


@pytest.mark.usefixtures("mock_clients")
def test_cluster_with_pattern_config_and_site_option_without_site_variable(
    user_config_file, runner
):
    user_config_file.write_text(
        """
    [general]
    cluster_hostname_pattern = my-{cluster}-cluster
    """
    )
    clients, command = _attach_sub_command(esok)

    r = runner.invoke(esok, ["-c", "favorite", "-s", "woops", command])

    assert r.exit_code == USER_ERROR, "Exit code should signal a user error."
    assert "Error" in r.output, "There should be error output explaining the issue."


@pytest.mark.usefixtures("mock_clients")
def test_cluster_with_pattern_config_and_missing_site(user_config_file, runner):
    user_config_file.write_text(
        """
    [general]
    cluster_hostname_pattern = my-{cluster}-{site}-cluster
    """
    )
    clients, command = _attach_sub_command(esok)

    r = runner.invoke(esok, ["-c", "favorite", command])

    assert r.exit_code == USER_ERROR, "Exit code should signal a user error."
    assert "Error" in r.output, "There should be error output explaining the issue."


@pytest.mark.usefixtures("mock_clients")
def test_cluster_with_pattern_config_and_default_sites(user_config_file, runner):
    user_config_file.write_text(
        """
    [general]
    cluster_hostname_pattern = my-{cluster}-{site}-cluster
    cluster_pattern_default_sites = site1,site2
    """
    )
    clients, command = _attach_sub_command(esok)

    r = runner.invoke(esok, ["-c", "favorite", command])

    assert r.exit_code == 0, "The command should succeed."
    assert (
        "my-favorite-site1-cluster" in clients
    ), "Specified cluster should be among the clients."
    assert (
        "my-favorite-site2-cluster" in clients
    ), "Specified cluster should be among the clients."
    assert "site1" in r.output, "CLI should indicate which site it is connecting to."
    assert "site2" in r.output, "CLI should indicate which site it is connecting to."


@pytest.mark.usefixtures("mock_clients")
def test_cluster_with_pattern_config_and_default_sites_without_site_variable(
    user_config_file, runner
):
    user_config_file.write_text(
        """
    [general]
    cluster_hostname_pattern = my-{cluster}-cluster
    cluster_pattern_default_sites = site1,site2
    """
    )
    clients, command = _attach_sub_command(esok)

    r = runner.invoke(esok, ["-c", "favorite", command])

    assert (
        r.exit_code == CONFIGURATION_ERROR
    ), "Exit code should signal a configuration error."
    assert "Error" in r.output, "There should be error output explaining the issue."


@pytest.mark.usefixtures("mock_clients")
def test_cluster_with_pattern_config_and_default_sites_and_site_option(
    user_config_file, runner
):
    user_config_file.write_text(
        """
    [general]
    cluster_hostname_pattern = my-{cluster}-{site}-cluster
    cluster_pattern_default_sites = site1,site2
    """
    )
    clients, command = _attach_sub_command(esok)

    r = runner.invoke(esok, ["-c", "favorite", "-s", "site3", command])

    assert r.exit_code == 0, "The command should succeed."
    assert [
        "my-favorite-site3-cluster"
    ] == clients, "Specified cluster should be the only client."


@pytest.mark.usefixtures("mock_clients")
def test_cluster_with_pattern_config_predefined_connections_takes_precedence(
    user_config_file, runner
):
    user_config_file.write_text(
        """
    [general]
    cluster_hostname_pattern = my-{cluster}-{site}-cluster
    cluster_pattern_default_sites = site1,site2
    [cluster:some-cluster]
    region2 = host1
    region1 = host2
    """
    )
    clients, command = _attach_sub_command(esok)

    r = runner.invoke(esok, ["-c", "some-cluster", command])

    assert r.exit_code == 0, "The command should succeed."
    assert "host1" in clients, "Specified cluster should be among the clients."
    assert "host2" in clients, "Specified cluster should be among the clients."
    assert "region1" in r.output, "CLI should indicate which site it is connecting to."
    assert "region2" in r.output, "CLI should indicate which site it is connecting to."


@pytest.mark.usefixtures("mock_clients")
def test_cluster_with_pattern_config_(user_config_file, runner):
    user_config_file.write_text(
        """
    [general]
    cluster_hostname_pattern = my-{cluster}-{site}-cluster
    cluster_pattern_default_sites = site1,site2
    [cluster:some-cluster]
    region2 = host1
    region1 = host2
    """
    )
    clients, command = _attach_sub_command(esok)

    r = runner.invoke(esok, ["-c", "some-cluster", command])

    assert r.exit_code == 0, "The command should succeed."
    assert "host1" in clients, "Specified cluster should be among the clients."
    assert "host2" in clients, "Specified cluster should be among the clients."
    assert "region1" in r.output, "CLI should indicate which site it is connecting to."
    assert "region2" in r.output, "CLI should indicate which site it is connecting to."


@pytest.mark.usefixtures("mock_clients")
def test_default_connection_can_be_predefined_connection(user_config_file, runner):
    user_config_file.write_text(
        """
    [general]
    default_connection = my-cluster
    [cluster:my-cluster]
    eu = host1
    us = host2
    """
    )
    clients, command = _attach_sub_command(esok)

    r = runner.invoke(esok, ["-s", "eu", command])

    assert r.exit_code == 0, "The command should succeed."
    assert "host1" in clients, "Specified cluster should be the only client."


@pytest.mark.usefixtures("mock_clients")
def test_cluster_with_pattern_config_and_default_sites_are_stripped_of_whitespace(
    user_config_file, runner
):
    user_config_file.write_text(
        """
    [general]
    cluster_hostname_pattern = my-{cluster}-{site}-cluster
    cluster_pattern_default_sites = site1, site2
    """
    )
    clients, command = _attach_sub_command(esok)

    r = runner.invoke(esok, ["-c", "favorite", command])

    assert r.exit_code == 0, "The command should succeed."
    assert (
        "my-favorite-site1-cluster" in clients
    ), "Specified cluster should be among the clients."
    assert (
        "my-favorite-site2-cluster" in clients
    ), "Specified cluster should be among the clients."


@pytest.mark.usefixtures("mock_clients")
def test_include_site_should_pass_site(user_config_file, runner):
    user_config_file.write_text(
        """
    [cluster:my-cluster]
    eu = host1
    us = host2
    """
    )
    clients = list()

    @esok.command()
    @per_connection(include_site=True)
    def sub(client, site):
        clients.append((client[1]["hosts"][0], site))

    r = runner.invoke(esok, ["-c", "my-cluster", "sub"])

    assert r.exit_code == 0, "The command should succeed."
    assert (
        "host1",
        "eu",
    ) in clients, "Configured site-to-host mapping should be preserved."
    assert (
        "host2",
        "us",
    ) in clients, "Configured site-to-host mapping should be preserved."


@pytest.mark.usefixtures("mock_clients")
def test_developer_boo_boo_is_captured(runner):
    """This happens if @connection_options and Click's context object is not set up properly,
    before @per_connection starts.
    """

    @click.group()
    def root():
        pass

    _, command = _attach_sub_command(root)

    r = runner.invoke(root, [command])

    assert r.exit_code == CLI_ERROR, "Exit code should signal an internal error."
    assert "Error" in r.output, "There should be error output explaining the issue."


@pytest.mark.usefixtures("mock_clients")
def test_progress_is_printed_for_several_clients(user_config_file, runner):
    user_config_file.write_text(
        """
    [cluster:awesome-cluster]
    eu = 192.168.0.1
    us = some.es.cluster.example.com
    ae = east-asia-host
    """
    )
    clients, command = _attach_sub_command(esok)

    r = runner.invoke(esok, ["-c", "awesome-cluster", command])

    assert r.exit_code == 0, "The command should succeed."
    assert (
        "awesome-cluster - eu:\n" in r.output
    ), "CLI should output which cluster it is connecting to."
    assert (
        "awesome-cluster - us:\n" in r.output
    ), "CLI should output which cluster it is connecting to."
    assert (
        "awesome-cluster - ae:\n" in r.output
    ), "CLI should output which cluster it is connecting to."
    assert "OK" in r.output, "CLI should indicate that command was successful."


@pytest.mark.usefixtures("mock_clients")
def test_no_progress_is_printed_for_only_one_client(user_config_file, runner):
    user_config_file.write_text(
        """
    [cluster:awesome-cluster]
    eu = 192.168.0.1
    """
    )
    clients, command = _attach_sub_command(esok)

    r = runner.invoke(esok, ["-c", "awesome-cluster", command])

    assert r.exit_code == 0, "The command should succeed."
    assert (
        r.output == ""
    ), "There should be no output when only one cluster is being connected to."


def test_bad_hostname(runner):
    clients, command = _attach_sub_command(esok)
    r = runner.invoke(esok, ["-H", "////////////////////", command])
    assert r.exit_code == USER_ERROR
    assert "Error" in r.output


@pytest.mark.usefixtures("mock_clients")
def test_tls(runner):
    clients, command = _attach_sub_command(esok, hostname_only=False)

    r = runner.invoke(esok, ["-T", command])
    assert r.exit_code == 0

    _, kwargs = clients[0]
    assert kwargs["use_ssl"] is True


@pytest.mark.usefixtures("mock_clients")
def test_ca_certificate(runner, test_app_dir):
    clients, command = _attach_sub_command(esok, hostname_only=False)
    ca_file = test_app_dir / "ca.crt"
    ca_file.touch()

    r = runner.invoke(esok, ["-C", str(ca_file), command])
    assert r.exit_code == 0

    _, kwargs = clients[0]
    assert kwargs["use_ssl"] is True
    assert kwargs["ssl_context"] == str(ca_file)


@pytest.mark.usefixtures("mock_clients")
def test_user_password_prompt(runner):
    clients, command = _attach_sub_command(esok, hostname_only=False)
    user = "super user"
    password = "super secret"

    r = runner.invoke(esok, ["-u", user, command], input=password)
    assert r.exit_code == 0

    _, kwargs = clients[0]
    assert kwargs["http_auth"] == (user, password)


@pytest.mark.usefixtures("mock_clients")
def test_timeout(runner):
    clients, command = _attach_sub_command(esok, hostname_only=False)
    timeout = 5

    r = runner.invoke(esok, ["-t", str(timeout), command])
    assert r.exit_code == 0

    _, kwargs = clients[0]
    assert kwargs["timeout"] == timeout


def _attach_sub_command(root_command, hostname_only=True):
    clients = list()

    @root_command.command()
    @per_connection()
    def sub(client):
        if hostname_only:
            clients.append(client[1]["hosts"][0])
        else:
            clients.append(client)

    return clients, sub.name


@pytest.fixture()
def mock_clients(monkeypatch):
    monkeypatch.setattr(
        "esok.config.connection_options.Elasticsearch",
        lambda *args, **kwargs: (args, kwargs),
    )
    monkeypatch.setattr(
        "esok.config.connection_options.create_default_context",
        lambda *args, cafile, **kwargs: cafile,
    )
