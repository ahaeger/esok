import logging

import click


class ConsoleFormatter(logging.Formatter):

    _traceback = False

    @property
    def show_traceback(self):
        return self._traceback

    @show_traceback.setter
    def show_traceback(self, value):
        self._traceback = value

    def format(self, record):
        msg = record.getMessage()
        if not self.is_info_level(record.levelno):
            level = record.levelname.capitalize()
            level_color = self.color_for_level(record.levelno)

            prefix = click.style(u"[{}] ".format(level), fg=level_color)
            msg = prefix + msg

        if self._traceback and record.exc_info:
            trace = self.formatException(record.exc_info)
            msg = msg + "\n" + trace

        return msg

    @staticmethod
    def is_info_level(level_number):
        return logging.INFO <= level_number < logging.WARNING

    @staticmethod
    def color_for_level(level_number):
        if level_number >= logging.ERROR:
            return "red"
        elif level_number >= logging.WARNING:
            return "yellow"
        elif level_number >= logging.INFO:
            return "white"
        else:
            return "blue"
