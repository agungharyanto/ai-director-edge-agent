import time
import cv2

from app.modules.video.frame_buffer import FrameBuffer
from app.modules.video.camera_worker import CameraWorker
from app.modules.vision.vision_pipeline import VisionPipeline


class VideoManager:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VideoManager, cls).__new__(cls)
            cls._instance.workers = {}
            cls._instance.buffers = {}
            cls._instance.pipeline = VisionPipeline()

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
                "stale": True,
                "frame_count": 0,
                "motion": 0,
                "player_detection": self.pipeline.is_player_enabled(camera_id),
                "player_count": self.pipeline.player_count(camera_id),
                "ball_detection": self.pipeline.is_ball_enabled(camera_id),
                "ball_count": self.pipeline.ball_count(camera_id),
                "ai_coordinates": self.get_ai_coordinates(camera_id),
                "rally": self.get_rally(camera_id),
                "director": self.get_director_decision(camera_id),
                "virtual_ptz": self.get_virtual_ptz_window(camera_id),
                "error": "Worker belum berjalan"
            }

        status = buffer.status()

        return {
            "online": status["online"],
            "last_update": status["last_update"],
            "stale": status.get("stale", False),
            "frame_count": status["frame_count"],
            "motion": worker.motion_count if worker else 0,
            "player_detection": self.pipeline.is_player_enabled(camera_id),
            "player_count": self.pipeline.player_count(camera_id),
            "ball_detection": self.pipeline.is_ball_enabled(camera_id),
            "ball_count": self.pipeline.ball_count(camera_id),
            "ai_coordinates": self.get_ai_coordinates(camera_id),
            "rally": self.get_rally(camera_id),
                "director": self.get_director_decision(camera_id),
                "virtual_ptz": self.get_virtual_ptz_window(camera_id),
            "error": status["error"]
        }

    def resize_frame(self, frame, width=960):
        h, w = frame.shape[:2]

        if w <= width:
            return frame

        ratio = width / float(w)
        height = int(h * ratio)

        return cv2.resize(frame, (width, height))

    def toggle_player_detection(self, camera_id):
        return self.pipeline.toggle_player(camera_id)

    def is_player_detection_enabled(self, camera_id):
        return self.pipeline.is_player_enabled(camera_id)

    def toggle_ball_detection(self, camera_id):
        return self.pipeline.toggle_ball(camera_id)

    def is_ball_detection_enabled(self, camera_id):
        return self.pipeline.is_ball_enabled(camera_id)

    def get_ai_coordinates(self, camera_id):
        return self.pipeline.get_coordinates(camera_id)

    def get_object_history(self, camera_id):
        return self.pipeline.get_object_history(camera_id)

    def get_ball_trajectory(self, camera_id):
        return self.pipeline.get_ball_trajectory(camera_id)

    def get_rally(self, camera_id):
        return self.pipeline.get_rally(camera_id)

    def get_director_decision(self, camera_id):
        return self.pipeline.get_director_decision(camera_id)

    def get_virtual_ptz_window(self, camera_id):
        return self.pipeline.get_virtual_ptz_window(camera_id)

    def mjpeg_generator(self, camera_id):
        while True:
            frame = self.get_frame(camera_id)

            if frame is None:
                time.sleep(0.05)
                continue

            frame = self.resize_frame(frame, width=960)
            frame = self.pipeline.process(camera_id, frame)

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
