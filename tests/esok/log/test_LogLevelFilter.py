import logging

import pytest

from esok.log.LogLevelFilter import LogLevelFilter


def test_filter_level_set_as_integer():
    filter = LogLevelFilter(20)

    okay_record = make_record(20)
    is_kept = filter.filter(okay_record)
    assert is_kept

    not_okay_record = make_record(21)
    is_kept = filter.filter(not_okay_record)
    assert not is_kept


def test_filter_level_set_as_string():
    filter = LogLevelFilter('INFO')

    okay_record = make_record(logging.INFO)
    is_kept = filter.filter(okay_record)
    assert is_kept

    not_okay_record = make_record(logging.INFO + 1)
    is_kept = filter.filter(not_okay_record)
    assert not is_kept


def test_filter_valid_level_strings():
    valid_levels = [
        (logging.DEBUG, 'DEBUG'),
        (logging.INFO, 'INFO'),
        (logging.WARNING, 'WARNING'),
        (logging.ERROR, 'ERROR'),
        (logging.CRITICAL, 'CRITICAL')
    ]

    for level_int, level_string in valid_levels:
        filter = LogLevelFilter(level_string)
        record = make_record(level_int)
        is_kept = filter.filter(record)
        assert is_kept


def test_fail_invalid_level_string():
    with pytest.raises(ValueError):
        LogLevelFilter('this is not a valid level')


def make_record(level):
    return logging.makeLogRecord({'levelno': level})
