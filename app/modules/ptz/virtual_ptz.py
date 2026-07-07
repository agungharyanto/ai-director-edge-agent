class VirtualPTZ:

    def __init__(self):
        self.last_window = {}

    def default_window(self):
        return {
            "x": 0.0,
            "y": 0.0,
            "w": 1.0,
            "h": 1.0,
            "zoom": 1.0
        }

    def decide_window(self, camera_id, director):
        action = director.get("action")

        if action == "FOLLOW_BALL_LEFT":
            window = {
                "x": 0.0,
                "y": 0.0,
                "w": 0.75,
                "h": 1.0,
                "zoom": 1.25
            }

        elif action == "FOLLOW_BALL_RIGHT":
            window = {
                "x": 0.25,
                "y": 0.0,
                "w": 0.75,
                "h": 1.0,
                "zoom": 1.25
            }

        elif action == "ZOOM_OUT":
            window = self.default_window()

        elif action == "CENTER":
            window = {
                "x": 0.125,
                "y": 0.0,
                "w": 0.75,
                "h": 1.0,
                "zoom": 1.2
            }

        else:
            window = self.default_window()

        self.last_window[camera_id] = window
        return window

    def get_window(self, camera_id):
        return self.last_window.get(camera_id, self.default_window())
