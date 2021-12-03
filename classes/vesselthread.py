from multiprocessing import Process
from typing import NoReturn, Optional

from classes.vessel import Vessel
from classes.remotefile import RemoteFile
from classes.retry import retry
from classes.database import Database
from classes.logger import Logger
from classes.file import File
from const import STATUS_COMPLETE, STATUS_START

import time


class VesselThread(Process):
    """Thread processing uploads to a single vessel
    """

    def __init__(self, vessel: Vessel, state: dict) -> None:
        """Initialize a new VesselThread

        Args:
            vessel (classes.vessel.Vessel): Vessel object to handle uploads for
            state (dict): Dictionary containing the current application state
        """
        super().__init__()
        self.vessel = vessel
        self._state = state
        self._logger = Logger()

    def run(self) -> NoReturn:
        """Run thread and process uploads to the vessel
        """
        self._logger.debug("Launched Vessel Thread for " + self.vessel.name)
        self.assertDirectories()
        while True:
            try:
                self.upload()
                time.sleep(5)
            except Exception as e:
                self._logger.error("An exception occurred in the Vessel Thread for " +
                                   self.vessel.name)
                self._logger.error(repr(e))

    @retry()
    def assertDirectories(self) -> None:
        for directory in self._state["config"].directories:
            if not directory.name in self.vessel._ignoredirs:
                self._logger.debug(
                    f"Making sure directory {directory.name} exists on Vessel {self.vessel.name}")
                self.vessel.connection.assertDirectories(directory)

    @retry()
    def upload(self) -> None:
        """Continue uploading process
        """
        if not (current := (self.vessel.currentUpload() or self.processQueue())):
            self._logger.debug(
                f"No file needs to be uploaded to Vessel {self.vessel.name} at the moment")
            return

        if isinstance(current, tuple):
            dirname, name, _ = current
            self._logger.debug(
                f"Found file {name} in directory {dirname} for vessel {self.vessel.name}")

            directory = None

            for d in self._state["config"].directories:
                if d.name == dirname:
                    directory = d
                    break

            if not directory:
                self._logger.debug(
                    f"Directory {dirname} not specified in config - deleting File from Vessel {self.vessel.name}")
                self.vessel.clearTempDir()
                return

            try:
                fileobj = File(name, directory)
            except FileNotFoundError:
                self._logger.debug(
                    f"File {name} does not exist in Directory {dirname} on shore - deleting from Vessel {self.name}")
                self.vessel.clearTempDir()
                return

        else:
            fileobj = current

        remotefile = RemoteFile(fileobj, self.vessel,
                                self._state["config"].chunksize)

        self._logger.debug(
            f"Start processing file {fileobj.name} in directory {fileobj.directory.name} on vessel {self.vessel.name}")

        while True:
            db = Database()
            if not db.getFileByUUID(fileobj.uuid):
                self._logger.debug(
                    f"File {fileobj.name} in directory {fileobj.directory.name} does not exist anymore - deleting from {self.vessel.name}")
                self.vessel.clearTempDir()
            del(db)

            self.vessel.assertDirectories(fileobj.directory)

            status = remotefile.getStatus()

            if status == STATUS_COMPLETE:
                self._logger.debug(
                    f"File {fileobj.name} uploaded to vessel {self.vessel.name} completely - finalizing")
                remotefile.finalizeUpload()

                db = Database()
                db.logCompletion(fileobj, self.vessel)
                del(db)

                self.vessel._uploaded.append(fileobj.uuid)
                self._logger.debug(
                    f"Moved {fileobj.name} to its final destination on {self.vessel.name} - done!")

                self.checkFileCompletion(fileobj)
                return

            nextchunk = 0 if status == STATUS_START else status + 1

            self._logger.debug(
                f"Getting chunk #{nextchunk} for file {fileobj.name} for vessel {self.vessel.name}")
            chunk = remotefile.getChunk(nextchunk)

            self._logger.debug("Got chunk")

            # If the Chunk has no data, the selected range is beyond the end
            # of the file, i.e. the complete file has already been uploaded

            if chunk.data:
                self._logger.debug(
                    f"Uploading chunk to vessel {self.vessel.name}")
                self.vessel.pushChunk(chunk)
            else:
                self._logger.debug(
                    f"No more data to upload to vessel {self.vessel.name} for file {fileobj.name} - compiling")
                self.vessel.compileComplete(remotefile)

    def checkFileCompletion(self, fileobj: File) -> None:
        db = Database()
        complete = db.getCompletionByFileUUID(fileobj.uuid)
        del(db)

        for vessel in self._state["config"].vessels:
            if vessel.name not in complete and fileobj.directory.name not in vessel._ignoredirs:
                return

        self._logger.debug(
            f"File {fileobj.name} from Directory {fileobj.directory.name} transferred to all Vessels. Moving out of replication directory.")
        fileobj.moveCompleted()

    def processQueue(self) -> Optional[str]:
        """Return a file from the processing queue
        """
        self._logger.debug(
            f"Trying to fetch new file for vessel {self.vessel.name} from queue")
        for f in self._state["files"]:
            if (not (f.uuid in self.vessel._uploaded)) and (not (f.directory.name in self.vessel._ignoredirs)):
                self._logger.debug(
                    f"Using file {f.name} for vessel {self.vessel.name}")
                return f
            if f.uuid in self.vessel._uploaded:
                reason = "already uploaded"
            else:
                reason = "Directory ignored"
            self._logger.debug(
                f"Disregarding file {f.name} for vessel {self.vessel.name} - {reason}")

        self._logger.debug(
            f"Didn't find any new files for vessel {self.vessel.name}")
