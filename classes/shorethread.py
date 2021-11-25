from classes.config import MonsterConfig
from classes.doghandler import DogHandler
from classes.directory import Directory
from classes.database import Database

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

    def purgeFile(self, directory: Directory, name: str) -> None:
        """Purge a removed File from the processing queue and database

        Args:
            directory (Directory): Directory (previously) containing the File
            name (str): Filename of the deleted File
        """
        # Remove file from processing queue
        for f in self._state["files"]:
            if f.directory == directory and f.name == name:
                del(f)

        # Remove file from database        
        db = Database()
        db.removeFile(directory, name)

    def addFile(self, fileobj):
        """Add a File object to the processing queue, if not already there

        Args:
            fileobj (classes.file.File): File object to add to the queue
        """
        found = False

        for f in self._state["files"]:
            if f.directory == fileobj.directory and f.name == fileobj.name:
                if f.uuid != fileobj.uuid:
                    del(f)
                else:
                    found = True

        if not found:
            self._state["files"].append(fileobj)

    def processFile(self, directory: Directory, name: str) -> None:
        """Process a file entry from the observer queue

        Args:
            directory (classes.directory.Directory): Directory containing the
              created, deleted, modified or moved File
            name (str): Filename of the created, deleted, modified or moved 
              File
        """
        if (fileobj := directory.getFile(name)):
            self.addFile(fileobj)
        else:
            self.purgeFile(directory, name)

    def processQueue(self) -> None:
        """Handle events currently on the queue

        N.B.: An event on the queue is a (directory, basename) tuple, where
        "directory" is a Directory object, and "basename" is the name of a
        File that has been created, moved, modified or deleted.
        """
        directory, basename = self.queue.get() # Will block until an event is found
        self.processFile(directory, basename)

    def terminate(self, *args, **kwargs) -> NoReturn:
        """Terminate observer threads, then terminate self
        """
        for dog in self._dogs:
            dog.terminate()
            dog.join()

        super().terminate(*args, **kwargs)
