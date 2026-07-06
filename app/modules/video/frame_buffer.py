import threading
import time


class FrameBuffer:

    def __init__(self):
        self.lock = threading.Lock()
        self.frame = None
        self.last_update = None
        self.frame_count = 0
        self.online = False
        self.error = None

    def set_frame(self, frame):
        with self.lock:
            self.frame = frame
            self.last_update = time.time()
            self.frame_count += 1
            self.online = True
            self.error = None

    def set_error(self, error):
        with self.lock:
            self.error = str(error)
            self.online = False

    def get_frame(self):
        with self.lock:
            return self.frame

    def status(self):
        with self.lock:
            return {
                "online": self.online,
                "last_update": self.last_update,
                "frame_count": self.frame_count,
                "error": self.error
            }
