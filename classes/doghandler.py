from watchdog.events import FileSystemEventHandler

import os.path


class DogHandler(FileSystemEventHandler):
    def __init__(self, directory, queue, *args, **kwargs):
        print("Initialized")
        super().__init__(*args, **kwargs)
        self._directory = directory
        self._queue = queue

    def dispatch(self, event):
        if not event.is_directory:
            super().dispatch(event)

    def on_created(self, event):
        self._queue.put((self._directory, os.path.basename(event.src_path)))

    def on_modified(self, event):
        self._queue.put((self._directory, os.path.basename(event.src_path)))

    def on_moved(self, event):
        self._queue.put((self._directory, os.path.basename(event.src_path)))
        self._queue.put((self._directory, os.path.basename(event.dest_path)))

    def on_deleted(self, event):
        self._queue.put((self._directory, os.path.basename(event.src_path)))
