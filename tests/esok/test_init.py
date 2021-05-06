from getpass import getuser

import pytest

from esok.constants import APP_CONFIG_BASENAME, DEFAULT_CONFIG
from esok.init import app_init

LOGS_DIR = "logs"


def test_copy_default_app_config(tmpdir):
    conf_path = tmpdir.join(APP_CONFIG_BASENAME)
    assert not conf_path.check()

    app_init(str(tmpdir))
    assert len(tmpdir.listdir()) == 2, u"Unexpected count of files."
    assert conf_path.check(), u"Config file is not where it is supposed to be."

    with conf_path.open() as config_file:
        with open(DEFAULT_CONFIG, u"r") as default_config:
            assert (
                config_file.read() == default_config.read()
            ), u"Config file contents are not the defaults."


def test_copy_default_app_config_already_exists(tmpdir):
    conf_path = tmpdir.join(APP_CONFIG_BASENAME)
    conf_path.ensure(file=True)

    app_init(str(tmpdir))

    with conf_path.open() as config_file:
        assert config_file.read() == u"", u"Existing file should not be overwritten."


@pytest.mark.skipif(
    getuser() == u"root",
    reason=u"Test does not work if running as root, like Tingle does.",
)
def test_init_app_no_write_permission(tmpdir, capsys):
    tmpdir.chmod(444)  # Only read permission

    app_init(str(tmpdir))  # Should swallow error

    _, err = capsys.readouterr()
    assert len(err) > 0, u"There should be error output, as files could not be written."


def test_init_dirs(tmpdir):
    path = tmpdir.join(LOGS_DIR)
    assert not path.check()

    app_init(str(tmpdir))

    assert path.check()


def test_init_logging(tmpdir):
    logs = tmpdir.mkdir(LOGS_DIR)

    app_init(str(tmpdir))

    assert len(logs.listdir()) == 4
    assert logs.join("info.log").check()
    assert logs.join("warning.log").check()
    assert logs.join("error.log").check()
    assert logs.join("all.log").check()
