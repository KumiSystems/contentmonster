import sqlite3
import pathlib
import uuid


class Database:
    def __init__(self, filename=None):
        filename = filename or pathlib.Path(
            __file__).parent.parent.absolute() / "database.sqlite3"
        self._con = sqlite3.connect(filename)
        self.migrate()

    def _execute(self, query, parameters=None):
        cur = self.getCursor()
        cur.execute(query, parameters)
        self.commit()

    def commit(self):
        return self._con.commit()

    def getCursor(self):
        return self._con.cursor()

    def getVersion(self):
        cur = self.getCursor()
        try:
            cur.execute(
                "SELECT value FROM contentmonster_settings WHERE key = 'dbversion'")
            assert (version := cur.fetchone())
            return int(version[0])
        except (sqlite3.OperationalError, AssertionError):
            return 0

    def getFileUUID(self, fileobj):
        hash = fileobj.getHash()

        cur = self.getCursor()
        cur.execute("SELECT uuid, checksum FROM contentmonster_file WHERE directory = ? AND name = ?",
                    (fileobj.directory.name, fileobj.name))

        fileuuid = None
        for result in cur.fetchall():
            if result[1] == hash:
                fileuuid = result[0]
            else:
                self.removeFileByUUID(result[0])

        return fileuuid or self.addFile(fileobj, hash)

    def addFile(self, fileobj, hash=None):
        hash = hash or fileobj.getHash()
        fileuuid = str(uuid.uuid4())
        self._execute("INSERT INTO contentmonster_file(uuid, directory, name, checksum) VALUES (?, ?, ?, ?)",
                      (fileuuid, fileobj.directory.name, fileobj.name, hash))
        return fileuuid

    def getFileByUUID(self, fileuuid):
        cur = self.getCursor()
        cur.execute(
            "SELECT directory, name, checksum FROM contentmonster_file WHERE uuid = ?", (fileuuid,))
        if (result := cur.fetchone()):
            return result

    def removeFileByUUID(self, fileuuid):
        self._execute(
            "DELETE FROM contentmonster_file WHERE uuid = ?", (fileuuid,))

    def logCompletion(self, file, vessel):
        self._execute(
            "INSERT INTO contentmonster_file_log(file, vessel) VALUES(?, ?)", (file.uuid, vessel.name))

    def getCompletionForVessel(self, vessel):
        cur = self.getCursor()
        cur.execute(
            "SELECT file FROM contentmonster_file_log WHERE vessel = ?", (vessel.name,))

    def migrate(self):
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
        self._con.close()
