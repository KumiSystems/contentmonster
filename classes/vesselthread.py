from multiprocessing import Process
from typing import NoReturn

from classes.vessel import Vessel

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

    def upload(self) -> None:
        """Continue uploading process
        """
        if not (current := self.vessel.currentUpload):
            self.processQueue()
            return
        pass

    def processQueue(self) -> None:
        """Start uploading a file from the processing queue
        """
        for f in self._state["files"]:
            if not f.uuid in self.vessel._uploaded:
                pass