#!/usr/bin/env python3

from classes.config import MonsterConfig
from classes.vesselthread import VesselThread

from multiprocessing import Manager

import pathlib

config_path = pathlib.Path(__file__).parent.absolute() / "settings.ini"

config = MonsterConfig.fromFile(settings_path)

