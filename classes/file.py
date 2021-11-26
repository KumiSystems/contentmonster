from classes.chunk import Chunk
from classes.database import Database

from typing import Optional

import hashlib
import os.path


class File:
    """Object representing a file found in a local Directory
    """

    def __init__(self, name: str, directory, uuid: Optional[str] = None) -> None:
        """Initialize new File object

        Args:
            name (str): Filename (basename without path) of the File to create
            directory (classes.directory.Directory): Directory object the File
              is located within
            uuid (str, optional): Unique identifier of this File object. Will
              be retrieved from database if None. Defaults to None.

        Raises:
            FileNotFoundError: Raised if the specified File does not exist
        """
        self.name = name
        self.directory = directory

        if not self.exists():
            raise FileNotFoundError(f"File {self.name} does not exist in {self.directory.name}!")

        self.uuid = uuid or self.getUUID()

    def exists(self) -> bool:
        """Check if the File exists on the local file system

        Returns:
            bool: True if the File exists, else False
        """
        return os.path.isfile(self.directory.location / self.name)

    def getUUID(self) -> str:
        """Return unique identifier for this File object

        Returns:
            str: File object's UUID retrieved from Database
        """
        db = Database()
        return db.getFileUUID(self)

    def getFullPath(self) -> str:
        """Get the full path of the File

        Returns:
            str: Full path of the File on the local file system
        """
        return self.directory.location / self.name

    def getHash(self) -> str:
        """Get hash for this File

        Returns:
            str: SHA256 for the full content of this File
        """
        return self.getChunk(-1).getHash()

    def getChunk(self, count: int, size: Optional[int] = None) -> Chunk:
        """Get a Chunk of this File

        Args:
            count (int): Position of the Chunk in a list of equally large
              Chunks (first index: 0). -1 represents a Chunk containing the
              complete file.
            size (int, optional): Size of the Chunk to create in Bytes. Must
              be set if count is not -1. Defaults to None.

        Returns:
            classes.chunk.Chunk: Chunk object containing File content from
              (count * size) bytes to ((count + 1) * size - 1) bytes

        Raises:
            ValueError: Raised if size is not set for a count that is not -1
        """
        if count != -1 and not size:
            raise ValueError(
                "A Chunk size needs to be passed to getChunk() if not using the complete file (-1)!")

        with open(self.getFullPath(), "rb") as binary:
            binary.seek((count * size) if count > 0 else 0)
            data = binary.read(size if count >= 0 else None)

        return Chunk(self, count, data)
