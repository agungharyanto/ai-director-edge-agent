import math


class BallTrajectory:

    def analyze(self, ball_points):
        if len(ball_points) < 2:
            return {
                "success": False,
                "state": "not_enough_data",
                "speed": 0,
                "direction": None
            }

        p1 = ball_points[-2]
        p2 = ball_points[-1]

        dx = p2["court_x"] - p1["court_x"]
        dy = p2["court_y"] - p1["court_y"]
        dt = max(p2["t"] - p1["t"], 0.001)

        distance = math.sqrt(dx * dx + dy * dy)
        speed = distance / dt

        if speed < 0.02:
            state = "stationary"
            direction = "none"
        elif abs(dx) > abs(dy):
            direction = "right" if dx > 0 else "left"
            state = "moving_" + direction
        else:
            direction = "down" if dy > 0 else "up"
            state = "moving_" + direction

        return {
            "success": True,
            "state": state,
            "direction": direction,
            "dx": round(dx, 4),
            "dy": round(dy, 4),
            "speed": round(speed, 4),
            "points": len(ball_points)
        }
