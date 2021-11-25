import hashlib


class Chunk:
    """A class defining a single chunk of a file to be uploaded"""

    @staticmethod
    def fromFile(fileobj, count: int, chunksize: int):
        """Create a new Chunk object from a File

        Args:
            fileobj (classes.file.File): The file object from local storage
            count (int): Position of the current chunk in the list of total
              chunks (first index: 0) or -1 to get the complete file
            chunksize (int): Size of each chunk in bytes

        Returns:
            classes.chunk.Chunk: A Chunk object containing the portion of the 
            File object beginning at (count * chunksize) bytes and ending at 
            ((count + 1) * chunksize - 1) bytes
        """
        return fileobj.getChunk(count, chunksize)

    def __init__(self, fileobj, count: int, data: bytes) -> None:
        """Initialize a new Chunk object

        Args:
            fileobj (classes.file.File): The file object from local storage
            count (int): Position of the current chunk in the list of total 
              chunks (first index: 0) or -1 to get the complete file
            data (bytes): Content of the chunk
        """
        self.file = fileobj
        self.count = count if count >= 0 else "complete"
        self.data = data

    def getTempName(self) -> str:
        """Get filename for this Chunk in the temp directory on the Vessel

        Returns:
            str: Filename to use for this chunk in the Vessel tempdir
        """
        return f"{self.file.uuid}_{self.count}.part"

    def getHash(self) -> str:
        """Generate a hash for this Chunk

        Returns:
            str: SHA256 hash of Chunk.data
        """
        return hashlib.sha256(self.data).hexdigest()
