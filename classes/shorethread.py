from classes.config import MonsterConfig
from classes.doghandler import DogHandler

from watchdog.observers import Observer

from multiprocessing import Process, Queue

import time

class ShoreThread:
    def __init__(self, files):
        super().__init__()
        self._config = MonsterConfig()
        self._dogs = []
        self.files = files
        self.queue = Queue()

    def getAllFiles(self):
        files = []

        for directory in self._config.directories:
            files.append(directory.getFiles())

        return files

    def clearFiles(self):
        del self.files[:]

    def monitor(self):
        for directory in self._config.directories:
            dog = DogHandler(self.queue)

            self._dogs.append(dog)

    def run(self):
        print("Launched Shore Thread")
        self.clearFiles()
