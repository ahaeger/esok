import logging

from click import BadParameter, echo

from esok.log.ConsoleFormatter import ConsoleFormatter


class ConsoleHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        """
        A log handler that is tuned for logging directly to the console, which
        directly sets up a ``esok.log.ClickFormatter`` formatter.

        :param level: The initial log level
        """
        super(ConsoleHandler, self).__init__(
            logging.NOTSET
        )  # Initialize so we can set formatter
        self.setFormatter(ConsoleFormatter())
        self.setLevel(level)

    def setLevel(self, level):
        level = self._check_level(level)
        try:
            super(ConsoleHandler, self).setLevel(level)
        except Exception:
            raise BadParameter(u"Verbosity level not recognized.")

    def emit(self, record):
        # noinspection PyBroadException
        try:
            msg = self.format(record)
            use_stderr = record.levelno >= logging.ERROR
            echo(msg, err=use_stderr)

        except Exception:
            self.handleError(record)

    def _check_level(self, level):
        if isinstance(level, str):
            level = level.upper()

            if level == u"EXCEPTION":
                level = logging.ERROR
                self.formatter.show_traceback = True
            else:
                self.formatter.show_traceback = False

        return level
