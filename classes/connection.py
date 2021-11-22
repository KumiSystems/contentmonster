import paramiko as pikuniku # :P

from paramiko.client import SSHClient

from io import BytesIO

import errno
import stat

class Connection:
    def __init__(self, vessel):
        self._vessel = vessel
        self._client = SSHClient()
        self._client.load_system_host_keys()
        self._client.connect(vessel.address)
        self._transport = self._client.get_transport()
        self._transport.set_keepalive(10)
        self._sftp = self._client.open_sftp()

    def _exists(self, path):
        try:
            self._sftp.stat(str(path))
            return True
        except FileNotFoundError:
            return False

    def _isdir(self, path):
        return stat.S_ISDIR(self._sftp.lstat(str(path)).st_mode)

    def _mkdir(self, path):
        return self._sftp.mkdir(str(path))

    def _listdir(self, path=None):
        return self._sftp.listdir(str(path) if path else None)

    def _remove(self, path):
        return self._sftp.remove(str(path))

    def assertDirectories(self, directory):
        for d in [directory, self._vessel.tempdir]:
            if not self._exists(d):
                self._mkdir(d)
            elif not self._isdir(d):
                raise ValueError(f"{d} exists but is not a directory on Vessel {self._vessel.name}!")

    def assertChunkComplete(self, chunk, path=None):
        path = path or self._vessel.tempdir / chunk.getTempName()

        if self._exists(path):
            _,o,_ = self._client.exec_command("sha256sum -b " + str(path))
            o.channel.recv_exit_status()
            if not o.readline().split()[0] == chunk.getHash():
                self._remove(path)
            else:
                return True
        return False

    def pushChunk(self, chunk):
        path = self._vessel.tempdir / chunk.getTempName()
        flo = BytesIO(chunk.data)
        self._sftp.putfo(flo, path, len(chunk.data))

    def compileComplete(self, remotefile):
        numchunks = remotefile.getStatus() + 1
        files = " ".join([str(self._vessel.tempdir / f"{remotefile.file.uuid}_{i}.part") for i in range(numchunks)])
        completefile = remotefile.file.getChunk(-1)
        outname = completefile.getTempName()
        outpath = self._vessel.tempdir / outname
        _,o,_ = self._client.exec_command(f"cat {files} > {outpath}")
        o.channel.recv_exit_status()

    def assertComplete(self, remotefile, allow_retry=False):
        completefile = remotefile.file.getChunk(-1)
        outname = completefile.getTempName()
        outpath = self._vessel.tempdir / outname

        if not self._exists(outpath):
            return False

        if not self.assertChunkComplete(completefile):
            if allow_retry:
                self._remove(outpath)
            else:
                self.clearTempDir()
            return False
        
        return True

    def moveComplete(self, remotefile):
        completefile = remotefile.file.getChunk(-1)
        destination = remotefile.getFullPath()
        self._sftp.rename(str(self._vessel.tempdir / completefile.getTempName()), str(destination))
        self._sftp.stat(str(destination))
        return True

    def getCurrentUploadUUID(self):
        for f in self._listdir(self._vessel.tempdir):
            if f.endswith(".part"):
                return f.split("_")[0]

    def clearTempDir(self):
        for f in self._listdir(self._vessel.tempdir):
            self._remove(self._vessel.tempdir / f)

    def __del__(self):
        self._client.close()