from watchdog.events import (FileSystemEventHandler, FileSystemEvent,
                             FileCreatedEvent, FileDeletedEvent,
                             FileModifiedEvent, FileMovedEvent)

from multiprocessing import Queue

from classes.logger import Logger

import os.path
import time


class DogHandler(FileSystemEventHandler):
    """Class implementing a watchdog event handler
    """

    def __init__(self, directory, queue: Queue, *args, **kwargs) -> None:
        """Initialize a new DogHandler object

        Args:
            directory (classes.directory.Directory): Directory to watch
            queue (multiprocessing.Queue): Queue to put detected events on
        """
        super().__init__(*args, **kwargs)
        self._directory = directory
        self._queue = queue
        self._logger = Logger()

    def dispatch(self, event: FileSystemEvent):
        """Dispatch events to the appropriate event handlers

        Args:
            event (watchdog.events.FileSystemEvent): Event to handle
        """
        if not event.is_directory:
            super().dispatch(event)

    def on_created(self, event: FileCreatedEvent):
        """Put file creation events on the queue

        Args:
            event (watchdog.events.FileCreatedEvent): Event describing the
              created file
        """
        self._logger.debug(f"Detected creation event of {event.src_path}")

        size = os.path.getsize(event.src_path)
        time.sleep(5)
        if size == os.path.getsize(event.src_path):
            self._queue.put((self._directory, os.path.basename(event.src_path)))

    def on_modified(self, event: FileModifiedEvent):
        """Put file modification events on the queue

        Args:
            event (watchdog.events.FileModifiedEvent): Event describing the
              modified file
        """
        self._logger.debug(f"Detected modification event of {event.src_path}")

        size = os.path.getsize(event.src_path)
        time.sleep(5)
        if size == os.path.getsize(event.src_path):
            self._queue.put((self._directory, os.path.basename(event.src_path)))

    def on_moved(self, event: FileMovedEvent):
        """Put file move events on the queue

        Args:
            event (watchdog.events.FileMovedEvent): Event describing the moved
              file (source and destination)
        """
        self._logger.debug(
            f"Detected move event of {event.src_path} to {event.dest_path}")
        self._queue.put((self._directory, os.path.basename(event.src_path)))
        self._queue.put((self._directory, os.path.basename(event.dest_path)))

    def on_deleted(self, event: FileDeletedEvent):
        """Put file deletion events on the queue

        Args:
            event (watchdog.events.FileDeletedEvent): Event describing the
              deleted file
        """
        self._logger.debug(f"Detected deletion event of {event.src_path}")
        self._queue.put((self._directory, os.path.basename(event.src_path)))
