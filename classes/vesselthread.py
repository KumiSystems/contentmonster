from multiprocessing import Process

from classes.vessel import Vessel

import time

class VesselThread(Process):
    """Thread processing uploads to a single vessel
    """
    def __init__(self, vessel: Vessel, state: dict):
        """Initialize a new VesselThread

        Args:
            vessel (classes.vessel.Vessel): Vessel object to handle uploads for
            state (dict): Dictionary containing the current application state
        """
        super().__init__()
        self.vessel = vessel
        self._state = state

    def run(self):
        """Run thread and process uploads to the vessel
        """
        print("Launched Vessel Thread for " + self.vessel.name)
        while True:
            try:
                print(self._state["files"][0])
            except:
                pass
            time.sleep(1)