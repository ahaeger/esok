import logging

from esok.log.decorator import debug, verbose, error, exception, critical, silence

_META_HANDLER_KEY = "esok.log.decorator.logHandler"


def test_debug():
    ctx, handler = _setup_mock()

    debug(ctx, None, False)
    assert handler.level is None

    debug(ctx, None, True)
    assert handler.level == logging.DEBUG


def test_verbose():
    ctx, handler = _setup_mock()

    verbose(ctx, None, False)
    assert handler.level is None

    verbose(ctx, None, True)
    assert handler.level == logging.INFO


def test_error():
    ctx, handler = _setup_mock()

    error(ctx, None, False)
    assert handler.level is None

    error(ctx, None, True)
    assert handler.level == logging.ERROR


def test_exception():
    ctx, handler = _setup_mock()

    exception(ctx, None, False)
    assert handler.level is None

    exception(ctx, None, True)
    assert handler.level == "EXCEPTION"


def test_critical():
    ctx, handler = _setup_mock()

    critical(ctx, None, False)
    assert handler.level is None

    critical(ctx, None, True)
    assert handler.level == logging.CRITICAL


def test_silence():
    ctx, handler = _setup_mock()

    silence(ctx, None, False)
    assert handler.level is None

    silence(ctx, None, True)
    assert handler.level >= logging.CRITICAL


def _setup_mock():
    handler = HandlerMock()
    ctx = ContextMock()
    ctx.meta[_META_HANDLER_KEY] = handler
    return ctx, handler


class HandlerMock(object):
    level = None

    def setLevel(self, lvl):
        self.level = lvl


class ContextMock(object):
    meta = dict()
