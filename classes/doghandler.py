from watchdog.events import FileSystemEventHandler

class DogHandler(FileSystemEventHandler):
    def __init__(self, queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._queue = queue

    def on_created(self, event):
        self._queue.put("Created: " + event.src_path)

    def on_modified(self, event):
        self._queue.put("Modified: " + event.src_path)

    def on_moved(self, event):
        self._queue.put("Moved: " + event.src_path + " to: " + event.dest_path)

    def on_deleted(self, event):
        self._queue.put("Deleted: " + event.src_path)