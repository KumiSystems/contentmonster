import hashlib

class Chunk:
    def __init__(self, fileobj, count, data):
        self.file = fileobj
        self.count = count if count >= 0 else "complete"
        self.data = data

    def getTempName(self):
        return f"{self.file.uuid}_{self.count}.part"

    def getHash(self):
        return hashlib.sha256(self.data).hexdigest()