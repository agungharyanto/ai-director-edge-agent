import time

from app.modules.detector.player_detector import PlayerDetector
from app.modules.detector.ball_detector import BallDetector
from app.modules.tracking.centroid_tracker import CentroidTracker
from app.modules.court.court_mapper import CourtMapper
from app.repositories.court_repository import CourtRepository
from app.modules.history.object_history import ObjectHistory
from app.modules.trajectory.ball_trajectory import BallTrajectory


class VisionPipeline:

    def __init__(self):
        self.player_detector = None
        self.ball_detector = None

        self.player_enabled = {}
        self.ball_enabled = {}

        self.last_player_detection_at = {}
        self.last_ball_detection_at = {}

        self.latest_player_detections = {}
        self.latest_ball_detections = {}

        self.player_trackers = {}
        self.court_mapper = CourtMapper()
        self.latest_coordinates = {}
        self.object_history = ObjectHistory()
        self.ball_trajectory = BallTrajectory()

    def get_player_detector(self):
        if self.player_detector is None:
            self.player_detector = PlayerDetector()
        return self.player_detector

    def get_ball_detector(self):
        if self.ball_detector is None:
            self.ball_detector = BallDetector()
        return self.ball_detector

    def get_player_tracker(self, camera_id):
        if camera_id not in self.player_trackers:
            self.player_trackers[camera_id] = CentroidTracker()
        return self.player_trackers[camera_id]

    def toggle_player(self, camera_id):
        current = self.player_enabled.get(camera_id, False)
        self.player_enabled[camera_id] = not current
        return self.player_enabled[camera_id]

    def toggle_ball(self, camera_id):
        current = self.ball_enabled.get(camera_id, False)
        self.ball_enabled[camera_id] = not current
        return self.ball_enabled[camera_id]

    def is_player_enabled(self, camera_id):
        return self.player_enabled.get(camera_id, False)

    def is_ball_enabled(self, camera_id):
        return self.ball_enabled.get(camera_id, False)

    def player_count(self, camera_id):
        return len(self.latest_player_detections.get(camera_id, []))

    def ball_count(self, camera_id):
        return len(self.latest_ball_detections.get(camera_id, []))

    def process(self, camera_id, frame):
        output = frame

        if self.is_player_enabled(camera_id):
            output = self.process_player(camera_id, output)

        if self.is_ball_enabled(camera_id):
            output = self.process_ball(camera_id, output)

        self.update_coordinates(camera_id)
        self.update_history(camera_id)

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

    def process_ball(self, camera_id, frame):
        now = time.time()
        last = self.last_ball_detection_at.get(camera_id, 0)

        if now - last >= 0.25:
            detections = self.get_ball_detector().detect(frame.copy())

            self.latest_ball_detections[camera_id] = detections
            self.last_ball_detection_at[camera_id] = now

        detections = self.latest_ball_detections.get(camera_id, [])

        return self.get_ball_detector().draw(frame, detections)


    def update_coordinates(self, camera_id):
        calibration = CourtRepository().get_camera_calibration(camera_id)

        if calibration is None:
            self.latest_coordinates[camera_id] = {
                "success": False,
                "error": "Calibration belum tersedia",
                "players": [],
                "balls": []
            }
            return

        players = []
        for det in self.latest_player_detections.get(camera_id, []):
            mapped = self.court_mapper.map_detection(calibration, det)
            players.append({
                "track_id": mapped.get("track_id"),
                "confidence": mapped.get("confidence"),
                "court_x": mapped.get("court_x"),
                "court_y": mapped.get("court_y")
            })

        balls = []
        for det in self.latest_ball_detections.get(camera_id, []):
            mapped = self.court_mapper.map_detection(calibration, det)
            balls.append({
                "confidence": mapped.get("confidence"),
                "court_x": mapped.get("court_x"),
                "court_y": mapped.get("court_y")
            })

        self.latest_coordinates[camera_id] = {
            "success": True,
            "players": players,
            "balls": balls
        }

    def get_coordinates(self, camera_id):
        return self.latest_coordinates.get(camera_id, {
            "success": False,
            "error": "No coordinate data",
            "players": [],
            "balls": []
        })


    def update_history(self, camera_id):
        coordinates = self.latest_coordinates.get(camera_id)

        if not coordinates or not coordinates.get("success"):
            return

        self.object_history.add_players(
            camera_id,
            coordinates.get("players", [])
        )

        self.object_history.add_balls(
            camera_id,
            coordinates.get("balls", [])
        )

    def get_object_history(self, camera_id):
        return {
            "success": True,
            "players": self.object_history.get_players(camera_id),
            "ball": self.object_history.get_ball(camera_id),
            "stats": self.object_history.stats(camera_id)
        }


    def get_ball_trajectory(self, camera_id):
        ball_points = self.object_history.get_ball(camera_id)
        return self.ball_trajectory.analyze(ball_points)
