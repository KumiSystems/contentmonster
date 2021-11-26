import paramiko as pikuniku  # :P

from paramiko.client import SSHClient, WarningPolicy

from io import BytesIO
from pathlib import Path
from typing import Union, Optional

import errno
import stat


class Connection:
    """Class representing an SSH/SFTP connection to a Vessel
    """

    def __init__(self, vessel):
        """Initialize a new Connection to a Vessel

        Args:
            vessel (classes.vessel.Vessel): Vessel object to open connection to
        """
        self._vessel = vessel
        self._client = SSHClient()
        self._client.load_system_host_keys()
        self._client.set_missing_host_key_policy(WarningPolicy)
        self._client.connect(vessel.address, vessel.port, vessel.username,
                             vessel.password, passphrase=vessel.passphrase)
        self._transport = self._client.get_transport()
        self._transport.set_keepalive(10)
        self._sftp = self._client.open_sftp()

    def _exists(self, path: Union[str, Path]) -> bool:
        """Check if a path exists on the Vessel. Symlinks are not followed.

        Args:
            path (str, pathlib.Path): Path to check on the vessel

        Returns:
            bool: True if the path exists on the Vessel, else False
        """
        try:
            self._sftp.stat(str(path))
            return True
        except FileNotFoundError:
            return False

    def _isdir(self, path: Union[str, Path]) -> bool:
        """Check if a path is a directory on the Vessel. Symlinks are followed.

        Args:
            path (str, pathlib.Path): Path to check on the vessel

        Returns:
            bool: True if the path provided is a directory on the Vessel, False
              if it is a different kind of file.

        Raises:
            FileNotFoundError: Raised if the path does not exist on the Vessel
        """
        return stat.S_ISDIR(self._sftp.lstat(str(path)).st_mode)

    def _mkdir(self, path: Union[str, Path]) -> None:
        """Create new directory on the Vessel

        Args:
            path (str, pathlib.Path): Path at which to create a new directory
              on the Vessel

        Raises:
            IOError: Raised if the directory cannot be created
        """
        self._sftp.mkdir(str(path))

    def _listdir(self, path: Optional[Union[str, Path]] = None) -> list[Optional[str]]:
        """List files in a directory on the Vessel

        Args:
            path (str, pathlib.Path, optional): Path at which to list contents.
              Will use current working directory if None. Defaults to None.

        Returns:
            list: List of the names of files (str) located at the provided path
        """
        return self._sftp.listdir(str(path) if path else ".")

    def _remove(self, path: Union[str, Path]) -> None:
        """Remove a file from the Vessel

        Args:
            path (str, pathlib.Path): Path of the file to delete

        Raises:
            FileNotFoundError: Raised if no file is found at the given path
            IOError: Raised if the file cannot be deleted
        """
        return self._sftp.remove(str(path))

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
        for d in [directory, self._vessel.tempdir]:
            if not self._exists(d):
                self._mkdir(d)
            elif not self._isdir(d):
                raise ValueError(
                    f"{d} exists but is not a directory on Vessel {self._vessel.name}!")

    def assertChunkComplete(self, chunk, path: Optional[Union[str, Path]] = None) -> bool:
        """Check if a Chunk has been uploaded correctly

        Args:
            chunk (classes.chunk.Chunk): Chunk object to verify upload for
            path (str, pathlib.Path, optional): Optional path at which to 
              check. If None, will get default path from Chunk object. 
              Defaults to None.

        Returns:
            bool: True if file has been uploaded correctly, else False
        """
        path = path or self._vessel.tempdir / chunk.getTempName()

        if self._exists(path):
            # "-b" should not be required, but makes sure to use binary mode
            _, o, _ = self._client.exec_command("sha256sum -b " + str(path))

            # Blocking for the command to complete
            o.channel.recv_exit_status()

            # Remove the file if it is broken
            if not o.readline().split()[0] == chunk.getHash():
                self._remove(path)

            else:
                return True
        return False

    def pushChunk(self, chunk, path: Optional[Union[str, Path]] = None) -> None:
        """Push the content of a Chunk object to the Vessel

        Args:
            chunk (classes.chunk.Chunk): Chunk object containing the data to
              push to the Vessel
            path (str, pathlib.Path, optional): Path at which to store the
              Chunk on the Vessel. If None, use default location provided by
              Chunk object. Defaults to None.
        """
        path = path or (self._vessel.tempdir / chunk.getTempName())
        flo = BytesIO(chunk.data)
        self._sftp.putfo(flo, path, len(chunk.data))

    def compileComplete(self, remotefile) -> None:
        """Build a complete File from uploaded Chunks.

        Args:
            remotefile (classes.remotefile.RemoteFile): RemoteFile object
              describing the uploaded File
        """
        numchunks = remotefile.getStatus() + 1

        # Get files in correct order to concatenate
        files = " ".join(
            [str(self._vessel.tempdir / f"{remotefile.file.uuid}_{i}.part") for i in range(numchunks)])

        completefile = remotefile.file.getChunk(-1)
        outname = completefile.getTempName()
        outpath = self._vessel.tempdir / outname
        _, o, _ = self._client.exec_command(f"cat {files} > {outpath}")

        # Block for command to complete
        o.channel.recv_exit_status()

    def assertComplete(self, remotefile, allow_retry: bool = False) -> bool:
        """Check if File has been reassembled from Chunks correctly

        Args:
            remotefile (classes.remotefile.RemoteFile): RemoteFile object
              describing the uploaded File
            allow_retry (bool, optional): If True, assume that compileComplete
              failed for some other reason than corrupt Chunks, and only delete
              compiled file, else clear entire temporary directory. Defaults to
              False.

        Returns:
            bool: True if file was reassembled correctly, else False
        """
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

    def moveComplete(self, remotefile) -> None:
        """Moves reassembled file to output destination

        Args:
            remotefile (classes.remotefile.RemoteFile): RemoteFile object 
              describing the uploaded File.

        Returns:
            [type]: [description]
        """
        completefile = remotefile.file.getChunk(-1)
        destination = remotefile.getFullPath()
        self._sftp.rename(
            str(self._vessel.tempdir / completefile.getTempName()), str(destination))

        # Make sure that file has actually been created at destination
        self._sftp.stat(str(destination))

    def getCurrentUploadUUID(self) -> Optional[str]:
        """Get UUID of file currently being uploaded

        Returns:
            str, optional: UUID of the File being uploaded, if any, else None
        """
        for f in self._listdir(self._vessel.tempdir):
            if f.endswith(".part"):
                return f.split("_")[0]

    def clearTempDir(self) -> None:
        """Clean up the temporary directory on the Vessel
        """
        for f in self._listdir(self._vessel.tempdir):
            self._remove(self._vessel.tempdir / f)

    def __del__(self):
        """Close SSH connection when ending Connection
        """
        self._client.close()
