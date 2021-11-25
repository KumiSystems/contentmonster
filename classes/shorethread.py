from classes.config import MonsterConfig
from classes.doghandler import DogHandler

from watchdog.observers import Observer

from multiprocessing import Process, Queue

import time
import os.path


class ShoreThread:
    def __init__(self, files, directories):
        super().__init__()
        self._dogs = []
        self.files = files
        self.queue = Queue()
        self.directories = directories

    def getAllFiles(self):
        files = []

        for directory in self.directories:
            files.append(directory.getFiles())

        return files

    def clearFiles(self):
        del self.files[:]

    def monitor(self):
        for directory in self.directories:
            print("Creating dog for " + str(directory.location))
            handler = DogHandler(directory, self.queue)
            dog = Observer()
            dog.schedule(handler, str(directory.location), False)
            dog.start()
            self._dogs.append(dog)

    def run(self):
        print("Launched Shore Thread")
        self.getAllFiles()
        self.monitor()
        try:
            while True:
                self.joinDogs()
                self.processQueue()
        except KeyboardInterrupt:
            self.stop()
            raise

    def joinDogs(self):
        for dog in self._dogs:
            dog.join(1)

    def processQueue(self):
        event = self.queue.get()
        print(event)

    def stop(self):
        for dog in self._dogs:
            dog.stop()
            dog.join()
