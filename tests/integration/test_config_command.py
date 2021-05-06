from click.testing import CliRunner

from esok.esok import esok


def test_config_prints_correct_info(default_config_file):
    content = default_config_file.read_text()

    runner = CliRunner()
    result = runner.invoke(esok, ["config"])

    assert result.exit_code == 0
    assert str(default_config_file) in result.output
    assert content in result.output
