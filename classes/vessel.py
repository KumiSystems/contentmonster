from classes.connection import Connection

from paramiko.ssh_exception import SSHException

class Vessel:
    @classmethod
    def fromConfig(cls, config):
        if "Address" in config.keys():
            return cls(config.name.split()[1], config["Address"])
        else:
            raise ValueError("Definition for Vessel " + config.name.split()[1] + " does not contain Address!")

    def __init__(self, name: str, address: str):
        self.name = name
        self.address = address
        self._connection = None

    @property
    def connection(self):
        if self._connection:
            try:
                self._connection._listdir()
                return self._connection
            except SSHException:
                self._connection = None
        self._connection = Connection(self)

    def currentUpload()