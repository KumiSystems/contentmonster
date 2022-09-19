#!/usr/bin/env python3

from classes.config import MonsterConfig
from classes.vesselthread import VesselThread
from classes.shorethread import ShoreThread

from multiprocessing import Manager

import pathlib
import time

if __name__ == '__main__':
    config_path = pathlib.Path(__file__).parent.absolute() / "settings.ini"
    config = MonsterConfig()
    config.readFile(config_path)

    with Manager() as manager:
        state = manager.dict()
        state["files"] = manager.list()
        state["config"] = config

        threads = []

        for vessel in config.vessels:
            thread = VesselThread(vessel, state)
            thread.start()
            threads.append(thread)

        shore = ShoreThread(state)
        shore.start()

        while True:
            try:
                time.sleep(10)
            except KeyboardInterrupt:
                print("Keyboard interrupt received - stopping threads")
                shore.terminate()
                for thread in threads:
                    thread.terminate()
                exit()
