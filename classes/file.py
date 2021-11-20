from classes.chunk import Chunk
from classes.database import Database

import hashlib

class File:
    def getUUID(self):
        db = Database()
        db.getFileUUID(self)

    def __init__(self, name, directory, uuid=None):
        self.name = name
        self.directory = directory
        self.uuid = uuid or self.getUUID()

    def getFullPath(self):
        return self.directory / self.name

    def getHash(self):
        return self.getChunk(-1).getHash()

    def getChunk(self, count, size=1048576):
        with open(self.getFullPath(), "rb") as binary:
            binary.seek((count * size) if count > 0 else 0)
            data = binary.read(size if count >= 0 else None)

        return Chunk(self, count, data)