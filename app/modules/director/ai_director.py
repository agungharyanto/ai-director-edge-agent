class AIDirector:

    def decide(self, rally, trajectory):
        if not rally.get("active"):
            return {
                "action": "CENTER",
                "reason": "rally_not_active"
            }

        if not trajectory.get("success"):
            return {
                "action": "WAIT",
                "reason": "trajectory_not_ready"
            }

        speed = trajectory.get("speed", 0)
        direction = trajectory.get("direction")

        if speed > 0.8:
            return {
                "action": "ZOOM_OUT",
                "reason": "ball_fast",
                "speed": speed,
                "direction": direction
            }

        if direction == "left":
            return {
                "action": "FOLLOW_BALL_LEFT",
                "reason": "ball_moving_left",
                "speed": speed
            }

        if direction == "right":
            return {
                "action": "FOLLOW_BALL_RIGHT",
                "reason": "ball_moving_right",
                "speed": speed
            }

        return {
            "action": "CENTER",
            "reason": "default",
            "speed": speed,
            "direction": direction
        }
