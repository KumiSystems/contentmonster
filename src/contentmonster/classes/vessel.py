from .connection import Connection
from .database import Database
from .file import File

from paramiko.ssh_exception import SSHException

from configparser import SectionProxy
from typing import Optional, Union

import pathlib


class Vessel:
    """Class describing a Vessel (= a replication destination)
    """
    @classmethod
    def fromConfig(cls, config: SectionProxy, dbclass: type = Database):
        """Create Vessel object from a Vessel section in the Config file

        Args:
            config (configparser.SectionProxy): Vessel section defining a 
              Vessel
            dbclass (type): Class to use for database connections. Defaults to
              built-in Database using sqlite3.

        Raises:
            ValueError: Raised if section does not contain Address parameter

        Returns:
            classes.vessel.Vessel: Vessel object for the vessel specified in
              the config section
        """

        tempdir = None
        username = None
        password = None
        passphrase = None
        port = 22
        timeout = None
        ignoredirs = []

        if "TempDir" in config.keys():
            tempdir = config["TempDir"]

        if "Username" in config.keys():
            username = config["Username"]

        if "Password" in config.keys():
            password = config["Password"]

        if "Passphrase" in config.keys():
            passphrase = config["Passphrase"]

        if "Port" in config.keys():
            port = config["Port"]

        if "Timeout" in config.keys():
            timeout = config["Timeout"]

        if "IgnoreDirs" in config.keys():
            ignoredirs = [d.strip() for d in config["IgnoreDirs"].split(",")]

        if "Address" in config.keys():
            return cls(config.name.split()[1], config["Address"], username,
                       password, passphrase, port, timeout, tempdir, ignoredirs, dbclass)
        else:
            raise ValueError("Definition for Vessel " +
                             config.name.split()[1] + " does not contain Address!")

    def __init__(self, name: str, address: str, username: Optional[str] = None,
                 password: Optional[str] = None, passphrase: Optional[str] = None,
                 port: Optional[int] = None, timeout: Optional[int] = None,
                 tempdir: Optional[Union[str, pathlib.Path]] = None,
                 ignoredirs: list[Optional[str]] = [], dbclass: type = Database) -> None:
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
        self.username = username
        self.password = password
        self.passphrase = passphrase
        self.port = port or 22
        self.timeout = timeout or 10
        self._connection = None
        self._dbclass = dbclass
        self._uploaded = self.getUploadedFromDB()  # Files already uploaded
        self._ignoredirs = ignoredirs  # Directories not replicated to this vessel

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
                self._connection._listdir(".")
            except (SSHException, OSError):
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
        db = self._dbclass()
        return db.getCompletionForVessel(self)

    def currentUpload(self) -> Optional[tuple[str, str, str]]:
        """Get the File that is currently being uploaded to this Vessel

        Returns:
            tuple: A tuple consisting of (directory, name, checksum), where
              "directory" is the name of the Directory object the File is
              located in, "name" is the filename (basename) of the File and
              checksum is the SHA256 hash of the file at the time of insertion
              into the database.  None is returned if no such record is found.
        """
        self.assertTempDirectory()  # After a reboot, the tempdir may be gone

        db = self._dbclass()
        output = db.getFileByUUID(self.connection.getCurrentUploadUUID())
        del db

        return output

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
        self.connection.pushChunk(chunk, str(path) if path else None)

    def compileComplete(self, remotefile) -> None:
        """Build a complete File from uploaded Chunks.

        Args:
            remotefile (classes.remotefile.RemoteFile): RemoteFile object
              describing the uploaded File
        """
        self.connection.compileComplete(remotefile)

    def assertDirectories(self, directory) -> None:
        """Make sure that destination and temp directories exist on the Vessel

        Args:
            directory (classes.directory.Directory): Directory object
              representing the directory to check

        Raises:
            ValueError: Raised if a path is already in use on the vessel but
              not a directory.
            IOError: Raised if a directory that does not exist cannot be 
              created.
        """
        self.connection.assertDirectories(directory)

    def assertTempDirectory(self) -> None:
        """Make sure that the temp directory exists on the Vessel

        Raises:
            ValueError: Raised if the path is already in use on the vessel but
              is not a directory.
            IOError: Raised if the directory does not exist but cannot be 
              created.
        """
        self.connection.assertTempDirectory()
