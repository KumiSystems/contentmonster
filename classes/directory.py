from classes.file import File

import os
import pathlib

class Directory:
    @classmethod
    def fromConfig(cls, config):
        if "Location" in config.keys():
            return cls(config.name.split()[1], config["Location"])
        else:
            raise ValueError("Definition for Directory " + config.name.split()[1] + " does not contain Location!")

    def __init__(self, name, location):
        self.name = name

        if os.path.isdir(location):
            self.location = pathlib.Path(location)
        else:
            raise ValueError(f"Location {location} for Directory {name} does not exist or is not a directory.")

    def getFiles(self):
        files = [f for f in os.listdir(self.location) if os.path.isfile]
        return [File(f, self) for f in files]