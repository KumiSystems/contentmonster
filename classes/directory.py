from classes.file import File

import os
import pathlib

from configparser import SectionProxy
from typing import Union, Optional


class Directory:
    """Class representing a Directory on the local filesystem
    """
    @classmethod
    def fromConfig(cls, config: SectionProxy):
        """Create Directory object from a Directory section in the Config file

        Args:
            config (configparser.SectionProxy): Configuration section defining 
              a Directory

        Raises:
            ValueError: Raised if section does not contain Location parameter

        Returns:
            classes.directory.Directory: Directory object for the location
              specified in the config section
        """
        if "Location" in config.keys():
            return cls(config.name.split()[1], config["Location"])
        else:
            raise ValueError("Definition for Directory " +
                             config.name.split()[1] + " does not contain Location!")

    def __init__(self, name: str, location: Union[str, pathlib.Path]):
        """Initialize a new Directory object

        Args:
            name (str): Name of the Directory object
            location (str, pathlib.Path): Filesystem location of the Directory

        Raises:
            ValueError: Raised if passed location does not exist or is not a 
              directory
        """
        self.name = name

        if os.path.isdir(location):
            self.location = pathlib.Path(location)
        else:
            raise ValueError(
                f"Location {location} for Directory {name} does not exist or is not a directory.")

    def getFiles(self) -> list[File]:
        """Get all Files in Directory

        N.B.: Returns only Files that have a size greater than 0

        Returns:
            list: List of File objects for files within the Directory
        """
        files = [f for f in os.listdir(self.location) if os.path.isfile(
            self.location / f) and os.path.getsize(self.location / f)]
        return [File(f, self) for f in files]

    def getFile(self, name: str) -> Optional[File]:
        """Get a file in the Directory by name

        Args:
            name (str): Filename of the File to get

        Returns:
            File, optional: File object if the file was found, else None
        """

        try:
            return File(name, self)
        except FileNotFoundError:
            return None
