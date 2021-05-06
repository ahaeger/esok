import logging


class LogLevelFilter(logging.Filter):
    def __init__(self, level):
        """
        Filters out log messages higher than specified log level.

        :param level: The maximum log level to include.
        """
        super(LogLevelFilter, self).__init__()
        self.level = level

        if not isinstance(level, int):
            # Not an int, try to get level number
            self.level = logging.getLevelName(level.upper())

        if not isinstance(self.level, int):
            raise ValueError(u"Configured log level name is not recognized.")

    def filter(self, record):
        return record.levelno <= self.level
