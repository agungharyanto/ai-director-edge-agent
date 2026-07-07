import cv2
import threading
import time

from app.modules.vision.motion_detector import MotionDetector


class VideoWorker(threading.Thread):

    def __init__(self, camera_id, rtsp_url):
        super().__init__(daemon=True)

        self.camera_id = camera_id
        self.rtsp_url = rtsp_url

        self.running = False

        self.frame = None

        self.frame_count = 0

        self.last_update = None

        self.error = None

        self.detector = MotionDetector()

        self.motion_count = 0

    def run(self):

        self.running = True

        cap = cv2.VideoCapture(self.rtsp_url)

        if not cap.isOpened():
            self.error = "Tidak bisa membuka RTSP"
            return

        while self.running:

            ok, frame = cap.read()

            if not ok:
                self.error = "Frame gagal dibaca"
                time.sleep(1)
                continue

            frame, count = self.detector.detect(frame)

            self.motion_count = count

            self.frame = frame

            self.frame_count += 1

            self.last_update = time.time()

        cap.release()

    def stop(self):
        self.running = False
