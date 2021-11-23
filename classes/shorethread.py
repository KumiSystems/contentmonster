from classes.config import MonsterConfig
from classes.doghandler import DogHandler

from watchdog.observers import Observer

from multiprocessing import Process, Queue

import time

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
            handler = DogHandler(self.queue)
            dog = Observer()
            dog.schedule(handler, str(directory.location))
            dog.start()
            self._dogs.append(dog)

    def run(self):
        print("Launched Shore Thread")
        self.monitor()
        try:
            while True:
                self.processQueue()
        except KeyboardInterrupt:
            self.stop()
            raise

    def processQueue(self):
        if not self.queue.empty:
            event = self.queue.get()
            print(event)

    def stop(self):
        for dog in self._dogs:
            dog.kill()