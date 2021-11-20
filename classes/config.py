import configparser

from classes.vessel import Vessel
from classes.directory import Directory

class MonsterConfig:
    @classmethod
    def fromFile(cls, path):
        parser = configparser.ConfigParser()
        parser.read(path)

        if not "MONSTER" in parser.sections():
            raise ValueError("Config file does not contain a MONSTER section!")

        directories = []
        vessels = []

        for section in parser.sections():
            if section.startswith("Directory"):
                directories.append(Directory.fromConfig(parser[section]))
            elif section.startswith("Vessel"):
                vessels.append(Vessel.fromConfig(parser[section]))

    def __init__(self):
        pass