import logging

import click

from esok.log.ConsoleHandler import ConsoleHandler

_META_HANDLER_KEY = __name__ + ".logHandler"


def verbosity(logger, *names, **kwargs):
    """
    Adds a verbosity option to the decorated command.

    Inspired heavily by: https://github.com/click-contrib/click-log

    :param logger: The logger to use, either name or actual object.
    :param names: Name of the flag. Defaults to --verbosity.
    :param kwargs: Passed to ``click.option``
    """
    if not isinstance(logger, logging.Logger):
        logger = logging.getLogger(logger)

    if not names:
        names = [u"--verbosity"]

    kwargs.setdefault(u"default", u"WARNING")
    kwargs.setdefault(u"metavar", u"LVL")
    kwargs.setdefault(
        u"help",
        u"Log messages >= LVL will be displayed in console. LVL is one of CRITICAL, EXCEPTION, "
        u"ERROR, WARNING (default), INFO or DEBUG. EXCEPTION == ERROR, but includes stack "
        u"traces.",
    )
    kwargs.setdefault(u"expose_value", False)
    kwargs.setdefault(u"is_eager", True)
    kwargs.setdefault(u"show_default", True)

    handler = ConsoleHandler(logging.WARNING)

    def decorator(f):
        def set_level(ctx, _, value):
            # Adding handler here, as this needs to happen after
            # other logging configurations have been applied.
            logger.addHandler(handler)
            handler.setLevel(value)
            ctx.meta[_META_HANDLER_KEY] = handler

        return click.option(*names, callback=set_level, **kwargs)(f)

    return decorator


def debug(ctx, _, enabled):
    _set_level(ctx, enabled, logging.DEBUG)


def verbose(ctx, _, enabled):
    _set_level(ctx, enabled, logging.INFO)


def error(ctx, _, enabled):
    _set_level(ctx, enabled, logging.ERROR)


def exception(ctx, _, enabled):
    _set_level(ctx, enabled, "EXCEPTION")


def critical(ctx, _, enabled):
    _set_level(ctx, enabled, logging.CRITICAL)


def silence(ctx, _, enabled):
    # TODO (haeger) This should probably disable the handler somehow
    _set_level(ctx, enabled, logging.CRITICAL + 100)


def _set_level(ctx, enabled, level):
    if enabled:
        handler = ctx.meta[_META_HANDLER_KEY]
        handler.setLevel(level)
