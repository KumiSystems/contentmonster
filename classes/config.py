import configparser

from pathlib import Path
from typing import Union

from classes.vessel import Vessel
from classes.directory import Directory


class MonsterConfig:
    def readFile(self, path: Union[str, Path]) -> None:
        """Read .ini file into MonsterConfig object

        Args:
            path (str, pathlib.Path): Location of the .ini file to read
              (absolute or relative to the working directory)

        Raises:
            ValueError: Raised if the passed file is not a ContentMonster .ini
            IOError: Raised if the file cannot be read from the provided path
        """
        parser = configparser.ConfigParser()
        parser.read(str(path))

        if not "MONSTER" in parser.sections():
            raise ValueError("Config file does not contain a MONSTER section!")

        for section in parser.sections():
            # Read Directories from the config file
            if section.startswith("Directory"):
                self.directories.append(
                    Directory.fromConfig(parser[section]))

            # Read Vessels from the config file
            elif section.startswith("Vessel"):
                self.vessels.append(Vessel.fromConfig(parser[section]))

    def __init__(self) -> None:
        """Initialize a new (empty) MonsterConfig object
        """
        self.directories = []
        self.vessels = []
