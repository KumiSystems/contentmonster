from classes.config import MonsterConfig
from classes.doghandler import DogHandler
from classes.directory import Directory
from classes.database import Database
from classes.logger import Logger

from watchdog.observers import Observer

from multiprocessing import Process, Queue
from typing import NoReturn

import time
import os.path


class ShoreThread(Process):
    """Thread handling the discovery of shore-side file changes
    """
    def __init__(self, state: dict, dbclass: type = Database) -> None:
        """Create a new ShoreThread object

        Args:
            state (dict): Dictionary containing the application state
        """
        super().__init__()
        self._dogs = []
        self._state = state
        self.queue = Queue()
        self._logger = Logger()
        self._dbclass = dbclass

    def getAllFiles(self) -> list:
        """Return File objects for all files in all Directories

        Returns:
            list: List of all File objects discovered
        """
        self._logger.debug("Getting all files from Shore")

        files = []

        for directory in self._state["config"].directories:
            self._logger.debug(f"Getting all files in {directory.name}")
            for f in directory.getFiles():
                files.append(f)

        return files

    def clearFiles(self) -> None:
        """Clear the files variable in the application state
        """
        self._logger.debug("Clearing global files variable")
        del self._state["files"][:]

    def monitor(self) -> None:
        """Initialize monitoring of Directories specified in configuration
        """
        for directory in self._state["config"].directories:
            self._logger.debug("Creating dog for " + str(directory.location))
            handler = DogHandler(directory, self.queue)
            dog = Observer()
            dog.schedule(handler, str(directory.location), False)
            dog.start()
            self._dogs.append(dog)

    def run(self) -> NoReturn:
        """Launch the ShoreThread and start monitoring for file changes
        """
        self._logger.info("Launched Shore Thread")

        for f in self.getAllFiles():
            self._state["files"].append(f)

        self.monitor()

        while True:
            self.joinDogs()
            self.processQueue()

    def joinDogs(self) -> None:
        """Join observers to receive updates on the queue
        """
        self._logger.debug("Joining dogs")
        for dog in self._dogs:
            dog.join(1)

    def purgeFile(self, directory: Directory, name: str) -> None:
        """Purge a removed File from the processing queue and database

        Args:
            directory (Directory): Directory (previously) containing the File
            name (str): Filename of the deleted File
        """
        self._logger.debug(f"Purging file {name} from {directory.name}")

        # Remove file from processing queue
        outlist = []
        for f in self._state["files"]:
            if f.directory.name == directory.name and f.name == name:
                self._logger.debug(f"Found {name} in files queue, deleting.")
            else:
                outlist.append(f)

        self.clearFiles()
        
        for f in outlist:
            self._state["files"].append(f)

        # Remove file from database
        self._logger.debug(f"Purging file {name} from database")
        db = self._dbclass()
        db.removeFile(directory, name)

    def addFile(self, fileobj):
        """Add a File object to the processing queue, if not already there

        Args:
            fileobj (classes.file.File): File object to add to the queue
        """
        self._logger.debug(f"Adding file {fileobj.name} to directory {fileobj.directory.name}")

        outlist = []

        for f in self._state["files"]:
            if f.directory.name == fileobj.directory.name and f.name == fileobj.name:
                self._logger.debug(f"File {fileobj.name} already in processing queue")
                if f.uuid != fileobj.uuid:
                    self._logger.debug("UUID does not match - deleting entry")
                else:
                    self._logger.debug("Found duplicate - deleting")
            else:
                outlist.append(f)

        if self.checkFileCompletion(fileobj):
            self._logger.debug(f"File {fileobj.name} already transferred to all Vessels - not re-adding to queue")
        else:
            self._logger.debug(f"File {fileobj.name} not in processing queue (anymore) - adding")
            outlist.append(fileobj)

        self.clearFiles()

        for f in outlist:
            self._state["files"].append(f)

    def checkFileCompletion(self, fileobj: File) -> bool:
        db = self._dbclass()
        complete = db.getCompletionByFileUUID(fileobj.uuid)
        del(db)

        for vessel in self._state["config"].vessels:
            if vessel.name not in complete and fileobj.directory.name not in vessel._ignoredirs:
                return False

        if fileobj.exists():
            fileobj.moveCompleted()
            
        return True

    def processFile(self, directory: Directory, name: str) -> None:
        """Process a file entry from the observer queue

        Args:
            directory (classes.directory.Directory): Directory containing the
              created, deleted, modified or moved File
            name (str): Filename of the created, deleted, modified or moved 
              File
        """
        self._logger.debug(f"Processing change to file {name} in directory {directory.name}")
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
        self._logger.debug("Waiting for new changes...")
        directory, basename = self.queue.get() # Will block until an event is found
        self.processFile(directory, basename)

    def terminate(self, *args, **kwargs) -> NoReturn:
        """Terminate observer threads, then terminate self
        """
        self._logger.info("Terminating dogs and shore thread")
        for dog in self._dogs:
            dog.terminate()
            dog.join()

        super().terminate(*args, **kwargs)
