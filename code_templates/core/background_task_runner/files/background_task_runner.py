import threading


class BackgroundTaskRunner:
    def __init__(self):
        self._thread = None
        self._cancel_event = threading.Event()
        self._running = False

    def start(self, fn, *args, **kwargs):
        if self._running:
            return False
        self._cancel_event.clear()
        self._thread = threading.Thread(
            target=self._run, args=(fn, args, kwargs), daemon=True
        )
        self._thread.start()
        self._running = True
        return True

    def _run(self, fn, args, kwargs):
        try:
            fn(self._cancel_event, *args, **kwargs)
        finally:
            self._running = False

    def cancel(self):
        self._cancel_event.set()

    @property
    def is_running(self):
        return self._running
