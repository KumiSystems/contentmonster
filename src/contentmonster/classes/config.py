import configparser

from pathlib import Path
from typing import Union

from classes.vessel import Vessel
from classes.directory import Directory
from classes.database import Database


class MonsterConfig:
    def readFile(self, path: Union[str, Path], dbclass: type = Database) -> None:
        """Read .ini file into MonsterConfig object

        Args:
            path (str, pathlib.Path): Location of the .ini file to read
              (absolute or relative to the working directory)
            dbclass (type): Class to use for database connections. Defaults to
              built-in Database using sqlite3.

        Raises:
            ValueError: Raised if the passed file is not a ContentMonster .ini
            IOError: Raised if the file cannot be read from the provided path
        """
        parser = configparser.ConfigParser()
        parser.read(str(path))

        if not "MONSTER" in parser.sections():
            raise ValueError("Config file does not contain a MONSTER section!")

        try:
            self.database = parser["MONSTER"]["Database"]
        except KeyError:
            pass

        try:
            self.chunksize = int(parser["MONSTER"]["ChunkSize"])
        except KeyError:
            pass

        for section in parser.sections():
            # Read Directories from the config file
            if section.startswith("Directory"):
                self.directories.append(
                    Directory.fromConfig(parser[section]))

            # Read Vessels from the config file
            elif section.startswith("Vessel"):
                self.vessels.append(
                    Vessel.fromConfig(parser[section], dbclass))

    def __init__(self) -> None:
        """Initialize a new (empty) MonsterConfig object
        """
        self.directories = []
        self.vessels = []
        self.chunksize = 10485760  # Default: 10 MiB
        self.database = None  # Default: "database.sqlite3" in base directory
