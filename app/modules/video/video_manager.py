import time
import cv2

from app.modules.video.frame_buffer import FrameBuffer
from app.modules.video.camera_worker import CameraWorker
from app.modules.detector.player_detector import PlayerDetector


class VideoManager:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VideoManager, cls).__new__(cls)
            cls._instance.workers = {}
            cls._instance.buffers = {}
            cls._instance.player_detection_enabled = {}
            cls._instance.player_detector = None
            cls._instance.last_player_detection_at = {}
            cls._instance.latest_player_detections = {}

        return cls._instance

    def start_camera(self, camera):
        camera_id = camera["id"]
        rtsp_url = camera["rtsp_url"]

        if not rtsp_url:
            return False

        if camera_id in self.workers:
            return True

        buffer = FrameBuffer()

        worker = CameraWorker(
            camera_id=camera_id,
            rtsp_url=rtsp_url,
            frame_buffer=buffer
        )

        self.buffers[camera_id] = buffer
        self.workers[camera_id] = worker

        worker.start()

        return True

    def stop_camera(self, camera_id):
        worker = self.workers.get(camera_id)

        if worker:
            worker.stop()

        self.workers.pop(camera_id, None)
        self.buffers.pop(camera_id, None)

    def get_frame(self, camera_id):
        buffer = self.buffers.get(camera_id)

        if not buffer:
            return None

        return buffer.get_frame()

    def get_status(self, camera_id):
        buffer = self.buffers.get(camera_id)
        worker = self.workers.get(camera_id)

        if not buffer:
            return {
                "online": False,
                "last_update": None,
                "frame_count": 0,
                "motion": 0,
                "player_detection": self.is_player_detection_enabled(camera_id),
                "player_count": 0,
                "error": "Worker belum berjalan"
            }

        status = buffer.status()

        return {
            "online": status["online"],
            "last_update": status["last_update"],
            "frame_count": status["frame_count"],
            "motion": worker.motion_count if worker else 0,
            "player_detection": self.is_player_detection_enabled(camera_id),
            "player_count": len(self.latest_player_detections.get(camera_id, [])),
            "error": status["error"]
        }

    def resize_frame(self, frame, width=960):
        h, w = frame.shape[:2]

        if w <= width:
            return frame

        ratio = width / float(w)
        height = int(h * ratio)

        return cv2.resize(frame, (width, height))

    def get_player_detector(self):
        if self.player_detector is None:
            self.player_detector = PlayerDetector()

        return self.player_detector

    def toggle_player_detection(self, camera_id):
        current = self.player_detection_enabled.get(camera_id, False)
        self.player_detection_enabled[camera_id] = not current
        return self.player_detection_enabled[camera_id]

    def is_player_detection_enabled(self, camera_id):
        return self.player_detection_enabled.get(camera_id, False)

    def apply_player_detection(self, camera_id, frame):
        if not self.is_player_detection_enabled(camera_id):
            return frame

        now = time.time()
        last = self.last_player_detection_at.get(camera_id, 0)

        if now - last >= 1.0:
            detections = self.get_player_detector().detect(frame.copy())
            self.latest_player_detections[camera_id] = detections
            self.last_player_detection_at[camera_id] = now

        detections = self.latest_player_detections.get(camera_id, [])

        return self.get_player_detector().draw(frame, detections)

    def mjpeg_generator(self, camera_id):
        while True:
            frame = self.get_frame(camera_id)

            if frame is None:
                time.sleep(0.05)
                continue

            frame = self.resize_frame(frame, width=960)
            frame = self.apply_player_detection(camera_id, frame)

            ok, jpg = cv2.imencode(
                ".jpg",
                frame,
                [int(cv2.IMWRITE_JPEG_QUALITY), 70]
            )

            if not ok:
                time.sleep(0.05)
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + jpg.tobytes()
                + b"\r\n"
            )

            time.sleep(0.12)
