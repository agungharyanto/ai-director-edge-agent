import time

from app.modules.detector.player_detector import PlayerDetector
from app.modules.tracking.centroid_tracker import CentroidTracker


class VisionPipeline:

    def __init__(self):
        self.player_detector = None
        self.player_enabled = {}
        self.last_player_detection_at = {}
        self.latest_player_detections = {}
        self.player_trackers = {}

    def get_player_detector(self):
        if self.player_detector is None:
            self.player_detector = PlayerDetector()

        return self.player_detector

    def get_player_tracker(self, camera_id):
        if camera_id not in self.player_trackers:
            self.player_trackers[camera_id] = CentroidTracker()

        return self.player_trackers[camera_id]

    def toggle_player(self, camera_id):
        current = self.player_enabled.get(camera_id, False)
        self.player_enabled[camera_id] = not current
        return self.player_enabled[camera_id]

    def is_player_enabled(self, camera_id):
        return self.player_enabled.get(camera_id, False)

    def player_count(self, camera_id):
        return len(self.latest_player_detections.get(camera_id, []))

    def process(self, camera_id, frame):
        output = frame

        if self.is_player_enabled(camera_id):
            output = self.process_player(camera_id, output)

        return output

    def process_player(self, camera_id, frame):
        now = time.time()
        last = self.last_player_detection_at.get(camera_id, 0)

        if now - last >= 1.0:
            detections = self.get_player_detector().detect(frame.copy())
            detections = self.get_player_tracker(camera_id).update(detections)

            self.latest_player_detections[camera_id] = detections
            self.last_player_detection_at[camera_id] = now

        detections = self.latest_player_detections.get(camera_id, [])

        return self.get_player_detector().draw(frame, detections)
