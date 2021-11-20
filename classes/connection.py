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

    def _listdir(self, path):
        return self._sftp.listdir(str(path))

    def _remove(self, path):
        return self._sftp.remove(str(path))

    def assertTempDirectory(self, directory):
        for d in [directory, directory.tempdir]:
            if not self._exists(d):
                self._mkdir(d)
            elif not self._isdir(d):
                raise ValueError(f"{d} exists but is not a directory on Vessel {self._vessel.name}!")

    def assertChunkComplete(self, chunk):
        path = chunk.file.directory.tempdir / chunk.getTempName()

        if self._exists(path):
            _,o,_ = self._client.exec_command("sha256sum -b " + str(path))
            o.channel.recv_exit_status()
            if not o.readline().split()[0] == chunk.getHash():
                self._remove(path)
            else:
                return True
        return False

    def pushChunk(self, chunk):
        path = chunk.file.directory.tempdir / chunk.getTempName()
        flo = BytesIO(chunk.data)
        self._sftp.putfo(flo, path, len(chunk.data))

    def compileComplete(self, remotefile):
        numchunks = remotefile.getStatus() + 1
        files = " ".join([str(remotefile.file.directory.tempdir / f"{remotefile.file.uuid}_{i}.part") for i in range(numchunks)])
        completefile = remotefile.file.getChunk(-1)
        outname = completefile.getTempName()
        outpath = remotefile.file.directory.tempdir / outname
        _,o,_ = self._client.exec_command(f"cat {files} > {outpath}")
        o.channel.recv_exit_status()

        return self.assertChunkComplete(completefile)

    def __del__(self):
        self._client.close()