import sqlite3
import pathlib
import uuid

from typing import Union, Optional


class Database:
    """Class wrapping sqlite3 database connection 
    """

    def __init__(self, filename: Optional[Union[str, pathlib.Path]] = None):
        """Initialize a new Database object

        Args:
            filename (str, pathlib.Path, optional): Filename of the sqlite3
              database to use. If None, use "database.sqlite3" in project base
              directory. Defaults to None.
        """
        filename = filename or pathlib.Path(
            __file__).parent.parent.absolute() / "database.sqlite3"
        self._con = sqlite3.connect(filename)
        self.migrate()

    def _execute(self, query: str, parameters: Optional[tuple] = None) -> None:
        """Execute a query on the database

        Args:
            query (str): SQL query to execute
            parameters (tuple, optional): Parameters to use to replace
              placeholders in the query, if any. Defaults to None.
        """
        cur = self.getCursor()
        cur.execute(query, parameters)
        self.commit()  # Instantly commit after every (potential) write action

    def commit(self) -> None:
        """Commit the current database transaction

        N.B.: Commit instantly after every write action to make the database
        "thread-safe". Connections will time out if the database is locked for
        more than five seconds.
        """
        self._con.commit()

    def getCursor(self) -> sqlite3.Cursor:
        """Return a cursor to operate on the sqlite3 database

        Returns:
            sqlite3.Cursor: Cursor object to execute queries on
        """
        return self._con.cursor()

    def getVersion(self) -> int:
        """Return the current version of the ContentMonster database

        Returns:
            int: Version of the last applied database migration
        """
        cur = self.getCursor()
        try:
            cur.execute(
                "SELECT value FROM contentmonster_settings WHERE key = 'dbversion'")
            assert (version := cur.fetchone())
            return int(version[0])
        except (sqlite3.OperationalError, AssertionError):
            return 0

    def getFileUUID(self, fileobj) -> str:
        """Retrieve unique identifier for File object

        Args:
            fileobj (classes.file.File): File object to retrieve UUID for

        Returns:
            str: UUID for passed File object
        """
        hash = fileobj.getHash()

        cur = self.getCursor()
        cur.execute("SELECT uuid, checksum FROM contentmonster_file WHERE directory = ? AND name = ?",
                    (fileobj.directory.name, fileobj.name))

        fileuuid = None

        # If file with same name and directory exists
        for result in cur.fetchall():

            # If it has the same hash, it is the same file -> return its UUID
            if result[1] == hash:
                fileuuid = result[0]

            # If not, it is a file that can no longer exist -> delete it
            else:
                self.removeFileByUUID(result[0])

        # Return found UUID or generate a new one
        return fileuuid or self.addFile(fileobj, hash)

    def addFile(self, fileobj, hash: Optional[str] = None) -> str:
        """Adds a new File object to the database

        Args:
            fileobj (classes.file.File): File object to add to database
            hash (str, optional): Checksum of the file, if already known. 
              Defaults to None.

        Returns:
            str: UUID of the new File record
        """
        hash = hash or fileobj.getHash()
        fileuuid = str(uuid.uuid4())
        self._execute("INSERT INTO contentmonster_file(uuid, directory, name, checksum) VALUES (?, ?, ?, ?)",
                      (fileuuid, fileobj.directory.name, fileobj.name, hash))
        return fileuuid

    def getFileByUUID(self, fileuuid: str) -> Optional[tuple[str, str, str]]:
        """Get additional information on a File by its UUID

        Args:
            fileuuid (str): The UUID of the File to retrieve from the database

        Returns:
            tuple: A tuple consisting of (directory, name, checksum), where
              "directory" is the name of the Directory object the File is
              located in, "name" is the filename (basename) of the File and
              checksum is the SHA256 hash of the file at the time of insertion
              into the database.  None is returned if no such record is found.
        """
        cur = self.getCursor()
        cur.execute(
            "SELECT directory, name, checksum FROM contentmonster_file WHERE uuid = ?", (fileuuid,))
        if (result := cur.fetchone()):
            return result

    def removeFile(self, directory, name: str) -> None:
        """Remove a File from the database based on Directory and filename

        Args:
            directory (classes.directory.Directory): Directory object 
              containing the File to remove
            name (str): Filename of the File to remove
        """
        self._execute(
            "DELETE FROM contentmonster_file WHERE directory = ? AND name = ?", (directory.name, name))

    def removeFileByUUID(self, fileuuid: str) -> None:
        """Remove a File from the database based on UUID

        Args:
            fileuuid (str): The UUID of the File to remove from the database
        """
        self._execute(
            "DELETE FROM contentmonster_file WHERE uuid = ?", (fileuuid,))

    def logCompletion(self, file, vessel):
        """Log the completion of a File upload

        Args:
            file (classes.file.File): The File object that has been uploaded
            vessel (classes.vessel.Vessel): The Vessel the File has been 
              uploaded to
        """
        self._execute(
            "INSERT INTO contentmonster_file_log(file, vessel) VALUES(?, ?)", (file.uuid, vessel.name))

    def getCompletionForVessel(self, vessel) -> list[Optional[str]]:
        """Get completed uploads for a vessel

        Args:
            vessel (classes.vessel.Vessel): The Vessel object to retrieve
              uploaded files for

        Returns:
            list: List of UUIDs of Files that have been successfully uploaded
        """
        cur = self.getCursor()
        cur.execute(
            "SELECT file FROM contentmonster_file_log WHERE vessel = ?", (vessel.name,))

        return [f[0] for f in cur.fetchall()]

    def getCompletionByFileUUID(self, fileuuid: str) -> list[Optional[str]]:
        cur = self.getCursor()
        cur.execute("SELECT vessel FROM contentmonster_file_log WHERE file = ?", (fileuuid,))

        return [v[0] for v in cur.fetchall()]

    def migrate(self) -> None:
        """Apply database migrations
        """
        cur = self.getCursor()

        if self.getVersion() == 0:
            cur.execute(
                "CREATE TABLE IF NOT EXISTS contentmonster_settings(key VARCHAR(64) PRIMARY KEY, value TEXT)")
            cur.execute(
                "INSERT INTO contentmonster_settings(key, value) VALUES ('dbversion', '1')")
            self.commit()

        if self.getVersion() == 1:
            cur.execute(
                "CREATE TABLE IF NOT EXISTS contentmonster_file(uuid VARCHAR(36) PRIMARY KEY, directory VARCHAR(128), name VARCHAR(128), checksum VARCHAR(64))")
            cur.execute("CREATE TABLE IF NOT EXISTS contentmonster_file_log(file VARCHAR(36), vessel VARCHAR(128), PRIMARY KEY (file, vessel), FOREIGN KEY (file) REFERENCES contentmonster_files(uuid) ON DELETE CASCADE)")
            cur.execute(
                "UPDATE contentmonster_settings SET value = '2' WHERE key = 'dbversion'")
            self.commit()

    def __del__(self):
        """Close database connection on removal of the Database object
        """
        self._con.close()
