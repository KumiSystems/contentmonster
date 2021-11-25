from classes.connection import Connection
from classes.database import Database
from classes.file import File

from paramiko.ssh_exception import SSHException

from configparser import SectionProxy
from typing import Optional, Union

import pathlib


class Vessel:
    """Class describing a Vessel (= a replication destination)
    """
    @classmethod
    def fromConfig(cls, config: SectionProxy):
        """Create Vessel object from a Vessel section in the Config file

        Args:
            config (configparser.SectionProxy): Vessel section defining a 
              Vessel

        Raises:
            ValueError: Raised if section does not contain Address parameter

        Returns:
            classes.vessel.Vessel: Vessel object for the vessel specified in
              the config section
        """

        tempdir = None

        if "TempDir" in config.keys():
            tempdir = config["TempDir"]

        if "Address" in config.keys():
            return cls(config.name.split()[1], config["Address"], tempdir)
        else:
            raise ValueError("Definition for Vessel " +
                             config.name.split()[1] + " does not contain Address!")

    def __init__(self, name: str, address: str, tempdir: Optional[Union[str, pathlib.Path]]) -> None:
        """Initialize new Vessel object

        Args:
            name (str): Name of the Vessel
            address (str): Address (IP or resolvable hostname) of the Vessel
            tempdir (pathlib.Path, optional): Temporary upload location on the
              Vessel, to store Chunks in
        """
        self.name = name
        self.address = address
        self.tempdir = pathlib.Path(tempdir or "/tmp/.ContentMonster/")
        self._connection = None
        self._uploaded = self.getUploadedFromDB()  # Files already uploaded

    @property
    def connection(self) -> Connection:
        """Get a Connection to the Vessel

        Returns:
            classes.connection.Connection: SSH/SFTP connection to the Vessel
        """
        # If a connection exists
        if self._connection:
            try:
                # ... check if it is up
                self._connection._listdir()
            except SSHException:
                # ... and throw it away if it isn't
                self._connection = None

        # If no connection exists (anymore), set up a new one
        self._connection = self._connection or Connection(self)
        return self._connection

    def getUploadedFromDB(self) -> list[str]:
        """Get a list of files that have previously been uploaded to the Vessel

        Returns:
            list: List of UUIDs of Files that have been successfully uploaded
        """
        db = Database()
        return db.getCompletionForVessel(self)

    def currentUpload(self) -> File:
        """Get the File that is currently being uploaded to this Vessel

        Returns:
            classes.file.File: File object representing the file currently
              being uploaded
        """
        db = Database()
        directory, name, _ = db.getFileByUUID(
            fileuuid := self.connection.getCurrentUploadUUID())
        return File(name, directory, fileuuid)

    def clearTempDir(self) -> None:
        """Clean up the temporary directory on the Vessel 
        """
        self.connection.clearTempDir()

    def pushChunk(self, chunk, path: Optional[Union[str, pathlib.Path]] = None) -> None:
        """Push the content of a Chunk object to the Vessel

        Args:
            chunk (classes.chunk.Chunk): Chunk object containing the data to
              push to the Vessel
            path (str, pathlib.Path, optional): Path at which to store the
              Chunk on the Vessel. If None, use default location provided by
              Vessel configuration and name provided by Chunk object. Defaults
              to None.
        """
        self.connection.pushChunk(chunk, path)

    def compileComplete(self, remotefile) -> None:
        """Build a complete File from uploaded Chunks.

        Args:
            remotefile (classes.remotefile.RemoteFile): RemoteFile object
              describing the uploaded File
        """
        self.connection.compileComplete(remotefile)