from multiprocessing import Process
from typing import NoReturn, Optional

from classes.vessel import Vessel
from classes.remotefile import RemoteFile
from classes.retry import retry
from classes.database import Database
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

    def run(self) -> NoReturn:
        """Run thread and process uploads to the vessel
        """
        print("Launched Vessel Thread for " + self.vessel.name)
        while True:
            try:
                self.upload()
            except Exception as e:
                print("An exception occurred in the Vessel Thread for " +
                      self.vessel.name)
                print(repr(e))

    @retry()
    def upload(self) -> None:
        """Continue uploading process
        """
        if not (current := self.vessel.currentUpload() or self.processQueue()):
            return

        remotefile = RemoteFile(current, self.vessel,
                                self._state["config"].chunksize)

        while True:
            status = remotefile.getStatus()

            if status == STATUS_COMPLETE:
                remotefile.finalizeUpload()
                db = Database()
                db.logCompletion(current, self.vessel)
                return

            nextchunk = 0 if status == STATUS_START else status + 1

            chunk = remotefile.getChunk(nextchunk)

            # If the Chunk has no data, the selected range is beyond the end
            # of the file, i.e. the complete file has already been uploaded

            if chunk.data:
                self.vessel.pushChunk(chunk)
            else:
                self.vessel.compileComplete(remotefile)

    def processQueue(self) -> Optional[str]:
        """Return a file from the processing queue
        """
        for f in self._state["files"]:
            if not f.uuid in self.vessel._uploaded:
                return f
