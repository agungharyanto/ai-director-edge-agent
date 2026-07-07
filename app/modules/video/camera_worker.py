import os
import time
import threading

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
    "rtsp_transport;tcp|"
    "fflags;nobuffer|"
    "flags;low_delay|"
    "max_delay;500000"
)

import cv2

from app.modules.vision.motion_detector import MotionDetector


class CameraWorker:

    def __init__(self, camera_id, rtsp_url, frame_buffer):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.frame_buffer = frame_buffer
        self.running = False
        self.thread = None
        self.capture = None

        self.detector = MotionDetector()
        self.motion_count = 0
        self.frame_index = 0

        self.target_fps = 8
        self.detect_every = 4
        self.drop_frames = 3

    def start(self):
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(
            target=self.run,
            daemon=True
        )
        self.thread.start()

    def stop(self):
        self.running = False

        if self.capture:
            self.capture.release()
            self.capture = None

    def open_capture(self):
        cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return cap

    def run(self):
        frame_delay = 1.0 / self.target_fps

        while self.running:
            try:
                self.capture = self.open_capture()

                if not self.capture.isOpened():
                    self.frame_buffer.set_error("RTSP tidak bisa dibuka")
                    time.sleep(3)
                    continue

                while self.running:
                    start = time.time()

                    for _ in range(self.drop_frames):
                        self.capture.grab()

                    ok, frame = self.capture.read()

                    if not ok:
                        self.frame_buffer.set_error("Gagal membaca frame")
                        time.sleep(1)
                        break

                    self.frame_index += 1

                    if self.frame_index % self.detect_every == 0:
                        frame, motion = self.detector.detect(frame)
                        self.motion_count = motion

                    self.frame_buffer.set_frame(frame)

                    elapsed = time.time() - start
                    sleep_time = frame_delay - elapsed

                    if sleep_time > 0:
                        time.sleep(sleep_time)

                if self.capture:
                    self.capture.release()
                    self.capture = None

                time.sleep(2)

            except Exception as error:
                self.frame_buffer.set_error(error)
                time.sleep(3)
