from click.testing import CliRunner

from esok.esok import esok


def test_es():
    runner = CliRunner()
    result = runner.invoke(esok, [])
    assert result.exit_code == 0
