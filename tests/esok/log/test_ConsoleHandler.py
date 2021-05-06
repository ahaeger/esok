import logging

import pytest
from click import BadParameter

from esok.log.ConsoleFormatter import ConsoleFormatter
from esok.log.ConsoleHandler import ConsoleHandler

# Does not exist in logging for py27
_nameToLevel = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARN": logging.WARNING,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}


def test_sets_up_console_formatter():
    handler = ConsoleHandler()
    formatter = handler.formatter
    assert isinstance(formatter, ConsoleFormatter)


def test_valid_string_logging_levels():
    valid_logging_levels = _nameToLevel.keys()

    for level in valid_logging_levels:
        handler = ConsoleHandler(level)
        assert handler.level == logging.getLevelName(level)


def test_handles_lower_case_level():
    lower_case_levels = [level.lower() for level in _nameToLevel.keys()]

    for level in lower_case_levels:
        handler = ConsoleHandler(level)
        assert handler.level == logging.getLevelName(level.upper())


def test_handles_custom_exception_level():
    handler = ConsoleHandler("EXCEPTION")
    assert handler.level == logging.ERROR
    assert handler.formatter.show_traceback


def test_throws_exception_on_bad_level():
    with pytest.raises(BadParameter):
        ConsoleHandler("w00t level mate")

    handler = ConsoleHandler()
    with pytest.raises(BadParameter):
        handler.setLevel("log all the things")


def test_errors_use_stderr(capsys):
    record = logging.makeLogRecord({"levelno": logging.ERROR})
    message = "A log message"

    handler = ConsoleHandler()
    handler.format = lambda _: message  # Mock format call
    handler.emit(record)

    captured = capsys.readouterr()
    assert message in captured.err


def test_non_errors_use_stdout(capsys):
    record = logging.makeLogRecord({"levelno": logging.ERROR - 1})
    message = "A log message"

    handler = ConsoleHandler()
    handler.format = lambda _: message  # Mock format call
    handler.emit(record)

    captured = capsys.readouterr()
    assert message in captured.out
