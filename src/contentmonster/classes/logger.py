from logging import Logger as PyLogger


class Logger(PyLogger):
    def __init__(self, name="contentmonster"):
        super().__init__(name)