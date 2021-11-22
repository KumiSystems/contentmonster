from watchdog.events import FileSystemEventHandler

class DogHandler(FileSystemEventHandler):
    def __init__(self, queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._queue = queue

    def on_created(self, event):
        pass

    def on_modified(self, event):
        pass

    def on_moved(self, event):
        pass

    def on_deleted(self, event):
        pass