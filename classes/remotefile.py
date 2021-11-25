from const import STATUS_COMPLETE, STATUS_START


class RemoteFile:
    """Class describing the transfer status of a File to a Vessel
    """

    def __init__(self, fileobj, vessel, chunksize: int) -> None:
        """Initialize a new RemoteFile object

        Args:
            fileobj (classes.file.File): File object to transfer to a Vessel
            vessel (classes.vessel.Vessel): Vessel to transfer the File to
            chunksize (int): Size of a single Chunk to transfer
        """
        self.file = fileobj
        self.vessel = vessel
        self.chunksize = chunksize

    def getStatus(self) -> int:
        """Get the current transfer status

        Returns:
            int: Number of the last Chunk that was uploaded, or STATUS_COMPLETE
              (-1) if a file upload is complete and waiting for finalization,
              or STATUS_START (-2) if no Chunk has been uploaded yet
        """

        # Get all files in the vessel's tempdir

        ls = self.vessel.connection._listdir(self.vessel.tempdir)
        files = [f for f in ls if f.startswith(
            self.file.uuid) and f.endswith(".part")]

        # Find the file with the largest chunk number

        count = -1

        for f in files:
            part = f.split("_")[1].split(".")[0]
            if part == "complete":  # If a reassembled file is found
                if self.validateComplete(True): # and it is not broken
                    return STATUS_COMPLETE # the upload is complete

            # Else save the chunk number if it is larger than the previous
            count = max(count, int(part))

        # Find and return the largest non-corrupt chunk
        while count >= 0:
            if self.validateChunk(count):
                return count
            count -= 1

        # If no (more) files exist, we are just getting started
        return STATUS_START

    def validateChunk(self, count: int) -> bool:
        """Validate that a Chunk was uploaded correctly

        Args:
            count (int): Chunk number to validate

        Returns:
            bool: True if file has been uploaded correctly, else False
        """
        return self.vessel.connection.assertChunkComplete(self.getChunk(count))

    def validateComplete(self, allow_retry: bool = False):
        """Validate that the complete File was reassembled correctly

        Args:
            allow_retry (bool, optional): If True, assume that compileComplete
              failed for some other reason than corrupt Chunks, and only delete
              compiled file, else clear entire temporary directory. Defaults to
              False.

        Returns:
            bool: True if file was reassembled correctly, else False
        """
        return self.vessel.connection.assertComplete(self, allow_retry)

    def compileComplete(self) -> None:
        """Reassemble a complete File from the uploaded Chunks
        """
        self.vessel.connection.compileComplete(self)

    def getChunk(self, count: int):
        """Get a Chunk of the source file

        Args:
            count (int): Number of the Chunk to generate

        Returns:
            classes.chunk.Chunk: A Chunk object containing the portion of the 
            File object beginning at (count * chunksize) bytes and ending at
            ((count + 1) * chunksize - 1) bytes, with chunksize taken from the
            RemoteFile initialization value
        """
        return self.file.getChunk(count, self.chunksize)

    def finalizeUpload(self) -> None:
        """Move complete file to its final destination and clean up
        """
        self.vessel.connection.moveComplete(self)
        self.vessel.connection.clearTempDir()