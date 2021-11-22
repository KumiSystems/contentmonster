from multiprocessing import Process

import time

class VesselThread(Process):
    def __init__(self, vessel, files):
        super().__init__()
        self.vessel = vessel
        self.files = files

    def run(self):
        print("Launched Vessel Thread for " + self.vessel.name)
        while True:
            try:
                print(self.files[0])
            except:
                print("Nothing.")
            time.sleep(10)