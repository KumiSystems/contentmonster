import logging
import threading

from datetime import datetime


class Logger:
    @staticmethod
    def _format(message: str, severity: str) -> str:
        thread = threading.current_thread().name
        datestr = str(datetime.now())
        return f"{datestr} - {thread} - {severity} - {message}"

    def debug(self, message: str) -> None:
        print(self.__class__()._format(message, "DEBUG"))

    def info(self, message: str) -> None:
        print(self.__class__()._format(message, "INFO"))

    def error(self, message: str) -> None:
        print(self.__class__()._format(message, "ERROR"))