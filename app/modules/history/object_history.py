import time
from collections import defaultdict, deque


class ObjectHistory:

    def __init__(self, max_age_seconds=10, max_points=120):
        self.max_age_seconds = max_age_seconds
        self.max_points = max_points

        self.player_history = defaultdict(lambda: defaultdict(deque))
        self.ball_history = defaultdict(deque)

    def _cleanup_deque(self, items):
        now = time.time()

        while items and now - items[0]["t"] > self.max_age_seconds:
            items.popleft()

        while len(items) > self.max_points:
            items.popleft()

    def add_players(self, camera_id, players):
        for player in players:
            track_id = player.get("track_id")

            if track_id is None:
                continue

            point = {
                "t": time.time(),
                "track_id": track_id,
                "court_x": player.get("court_x"),
                "court_y": player.get("court_y"),
                "confidence": player.get("confidence")
            }

            history = self.player_history[camera_id][track_id]
            history.append(point)
            self._cleanup_deque(history)

    def add_balls(self, camera_id, balls):
        history = self.ball_history[camera_id]

        for ball in balls:
            point = {
                "t": time.time(),
                "court_x": ball.get("court_x"),
                "court_y": ball.get("court_y"),
                "confidence": ball.get("confidence")
            }

            history.append(point)

        self._cleanup_deque(history)

    def get_players(self, camera_id):
        result = []

        for track_id, history in self.player_history[camera_id].items():
            self._cleanup_deque(history)

            result.append({
                "track_id": track_id,
                "points": list(history)
            })

        return result

    def get_ball(self, camera_id):
        history = self.ball_history[camera_id]
        self._cleanup_deque(history)

        return list(history)

    def stats(self, camera_id):
        players = self.get_players(camera_id)
        ball = self.get_ball(camera_id)

        return {
            "player_tracks": len(players),
            "player_points": sum(len(p["points"]) for p in players),
            "ball_points": len(ball)
        }
