STATUS_START = -1
STATUS_COMPLETE = -2

class RemoteFile:
    def __init__(self, fileobj, vessel, chunksize=1048576):
        self.file = fileobj
        self.vessel = vessel
        self.chunksize = chunksize

    def getStatus(self):
        ls = self.vessel.connection._listdir(self.vessel.tempdir)
        files = [f for f in ls if f.startswith(self.file.uuid) and f.endswith(".part")]

        ids = [-1]

        for f in files:
            part = f.split("_")[1].split(".")[0]
            if part == "complete":
                if self.validateComplete():
                    return STATUS_COMPLETE
            ids.append(int(part))

        count = max(ids)

        while count >= 0:
            if self.validateChunk(count):
                return count
            count -=1
    
        return STATUS_START

    def validateChunk(self, count):
        return self.vessel.connection.assertChunkComplete(self.getChunk(count))

    def validateComplete(self):
        return self.validateChunk(-1)

    def compileComplete(self):
        self.vessel.connection.compileComplete(self)

    def getChunk(self, count):
        return self.file.getChunk(count, self.chunksize)