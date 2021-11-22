from classes.connection import Connection
from classes.database import Database
from classes.file import File

from paramiko.ssh_exception import SSHException

import pathlib

class Vessel:
    @classmethod
    def fromConfig(cls, config):
        if "TempDir" in config.keys():
            tempdir = config["TempDir"]
        else:
            tempdir = "/tmp/.ContentMonster/"
        if "Address" in config.keys():
            return cls(config.name.split()[1], config["Address"], pathlib.Path(tempdir))
        else:
            raise ValueError("Definition for Vessel " + config.name.split()[1] + " does not contain Address!")

    def __init__(self, name: str, address: str, tempdir: pathlib.Path):
        self.name = name
        self.address = address
        self.tempdir = tempdir
        self._connection = None
        self._uploaded = self.getUploadedFromDB()

    @property
    def connection(self):
        if self._connection:
            try:
                self._connection._listdir()
            except SSHException:
                self._connection = None
        self._connection = self._connection or Connection(self)
        return self._connection

    def getUploadedFromDB(self):
        db = Database()
        return db.getCompletionForVessel(self)

    def currentUpload(self):
        db = Database()
        directory, name, _ = db.getFileByUUID(fileuuid := self.connection.getCurrentUploadUUID())
        return File(name, directory, fileuuid)

    def clearTempDir(self):
        return self.connection.clearTempDir()