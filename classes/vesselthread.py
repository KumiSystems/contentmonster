from multiprocessing import Process

class VesselThread(Process):
    def __init__(self, vessel, files):
        super().__init__()
        self.vessel = vessel

    def run(self):
        pass