import time


class RallyEngine:

    def __init__(self):
        self.state = {}
        self.last_ball_seen = {}

    def update(self, camera_id, trajectory):
        now = time.time()

        if not trajectory.get("success"):
            return {
                "state": "WAITING_BALL",
                "active": False,
                "speed": 0
            }

        speed = trajectory.get("speed", 0)

        if speed > 0.30:
            self.state[camera_id] = "RALLY"
            self.last_ball_seen[camera_id] = now

            return {
                "state": "RALLY",
                "active": True,
                "speed": speed
            }

        last = self.last_ball_seen.get(camera_id)

        if last and now - last < 2.0:
            return {
                "state": "RALLY",
                "active": True,
                "speed": speed
            }

        self.state[camera_id] = "IDLE"

        return {
            "state": "IDLE",
            "active": False,
            "speed": speed
        }
