from classes.config import MonsterConfig
from classes.doghandler import DogHandler

from watchdog.observers import Observer

from multiprocessing import Process, Queue
from typing import NoReturn

import time
import os.path


class ShoreThread(Process):
    """Thread handling the discovery of shore-side file changes
    """
    def __init__(self, state: dict) -> None:
        """Create a new ShoreThread object

        Args:
            state (dict): Dictionary containing the application state
        """
        super().__init__()
        self._dogs = []
        self._state = state
        self.queue = Queue()

    def getAllFiles(self) -> list:
        """Return File objects for all files in all Directories

        Returns:
            list: List of all File objects discovered
        """
        files = []

        for directory in self._state["config"].directories:
            for f in directory.getFiles():
                files.append(f)

        return files

    def clearFiles(self) -> None:
        """Clear the files variable in the application state
        """
        del self._state["files"][:]

    def monitor(self) -> None:
        """Initialize monitoring of Directories specified in configuration
        """
        for directory in self._state["config"].directories:
            print("Creating dog for " + str(directory.location))
            handler = DogHandler(directory, self.queue)
            dog = Observer()
            dog.schedule(handler, str(directory.location), False)
            dog.start()
            self._dogs.append(dog)

    def run(self) -> NoReturn:
        """Launch the ShoreThread and start monitoring for file changes
        """
        print("Launched Shore Thread")
        self.getAllFiles()
        self.monitor()
        
        while True:
            self.joinDogs()
            self.processQueue()

    def joinDogs(self) -> None:
        """Join observers to receive updates on the queue
        """
        for dog in self._dogs:
            dog.join(1)

    def processQueue(self) -> None:
        """Handle events currently on the queue
        """
        event = self.queue.get() # Will block until an event is found
        print(event)

    def terminate(self, *args, **kwargs) -> None:
        """Terminate observer threads, then terminate self
        """
        for dog in self._dogs:
            dog.terminate()
            dog.join()

        super().terminate(*args, **kwargs)
