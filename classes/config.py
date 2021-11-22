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

        config = cls()

        for section in parser.sections():
            if section.startswith("Directory"):
                config.directories.append(Directory.fromConfig(parser[section]))
            elif section.startswith("Vessel"):
                config.vessels.append(Vessel.fromConfig(parser[section]))

        return config

    def __init__(self):
        self.directories = []
        self.vessels = []
