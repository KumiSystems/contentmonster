#!/usr/bin/env python3

from classes.config import MonsterConfig
from classes.vesselthread import VesselThread
from classes.shorethread import ShoreThread

from multiprocessing import Manager

import pathlib
import time

if __name__ == '__main__':
    config_path = pathlib.Path(__file__).parent.absolute() / "settings.ini"
    config = MonsterConfig.fromFile(config_path)

    with Manager() as manager:
        files = manager.list()

        threads = []

        for vessel in config.vessels:
            thread = VesselThread(vessel, files)
            thread.start()
            threads.append(thread)

        try:
            shore = ShoreThread(files)
            shore.run()
        except KeyboardInterrupt:
                print("Keyboard interrupt received - stopping threads")
                for thread in threads:
                    thread.kill()
                exit()