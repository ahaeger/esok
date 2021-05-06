import logging

import click

from esok.log.ConsoleFormatter import ConsoleFormatter


def test_notset_format():
    record_message = u"This is a test!"
    record = logging.makeLogRecord(
        {u"msg": record_message, u"levelno": logging.NOTSET, u"levelname": u"NOTSET"}
    )

    formatter = ConsoleFormatter()
    msg = formatter.format(record)

    prefix = click.style(u"[Notset] ", fg="blue")
    assert prefix + record_message == msg


def test_debug_format():
    record_message = u"This is a test!"
    record = logging.makeLogRecord(
        {u"msg": record_message, u"levelno": logging.DEBUG, u"levelname": u"DEBUG"}
    )

    formatter = ConsoleFormatter()
    msg = formatter.format(record)

    prefix = click.style(u"[Debug] ", fg="blue")
    assert prefix + record_message == msg


def test_info_format():
    record_message = u"This is a test!"
    record = logging.makeLogRecord({u"msg": record_message, u"levelno": logging.INFO})

    formatter = ConsoleFormatter()
    msg = formatter.format(record)

    assert record_message == msg


def test_warning_format():
    record_message = u"This is a test!"
    record = logging.makeLogRecord(
        {u"msg": record_message, u"levelno": logging.WARNING, u"levelname": u"WARNING"}
    )

    formatter = ConsoleFormatter()
    msg = formatter.format(record)

    prefix = click.style(u"[Warning] ", fg="yellow")
    assert prefix + record_message == msg


def test_error_format():
    record_message = u"This is a test!"
    record = logging.makeLogRecord(
        {u"msg": record_message, u"levelno": logging.ERROR, u"levelname": u"ERROR"}
    )

    formatter = ConsoleFormatter()
    msg = formatter.format(record)

    prefix = click.style(u"[Error] ", fg="red")
    assert prefix + record_message == msg


def test_critical_format():
    record_message = u"This is a test!"
    record = logging.makeLogRecord(
        {
            u"msg": record_message,
            u"levelno": logging.CRITICAL,
            u"levelname": u"CRITICAL",
        }
    )

    formatter = ConsoleFormatter()
    msg = formatter.format(record)

    prefix = click.style(u"[Critical] ", fg="red")
    assert prefix + record_message == msg


def test_error_format_with_traceback():
    record_message = u"This is a test!"
    record = logging.makeLogRecord(
        {
            u"msg": record_message,
            u"levelno": logging.ERROR,
            u"levelname": u"ERROR",
            u"exc_info": "Something",
        }
    )

    formatter = ConsoleFormatter()
    formatter.show_traceback = True
    tb_text = "Shitty traceback."
    formatter.formatException = lambda _: tb_text  # Mock traceback text
    msg = formatter.format(record)

    prefix = click.style(u"[Error] ", fg="red")
    expected = u"{}{}\n{}".format(prefix, record_message, tb_text)
    assert expected == msg


def test_is_info_level():
    assert not ConsoleFormatter.is_info_level(logging.INFO - 1)
    assert ConsoleFormatter.is_info_level(logging.INFO)
    assert ConsoleFormatter.is_info_level(logging.WARNING - 1)
    assert not ConsoleFormatter.is_info_level(logging.WARNING)


def test_color_for_level():
    assert ConsoleFormatter.color_for_level(logging.CRITICAL) == "red"
    assert ConsoleFormatter.color_for_level(logging.ERROR) == "red"
    assert ConsoleFormatter.color_for_level(logging.WARNING) == "yellow"
    assert ConsoleFormatter.color_for_level(logging.INFO) == "white"
    assert ConsoleFormatter.color_for_level(logging.DEBUG) == "blue"
    assert ConsoleFormatter.color_for_level(logging.NOTSET) == "blue"
