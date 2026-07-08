class VirtualPTZ:

    def __init__(self):
        self.last_window = {}

        # Gerakan halus, tidak agresif
        self.smoothing = 0.08

        # FIXED ZOOM
        # 1.0 = full frame
        # 0.80 = zoom 1.25x
        # 0.70 = zoom 1.43x
        self.fixed_width = 0.80
        self.fixed_height = 1.0

        # Dead zone agar kamera tidak geser untuk gerakan kecil
        self.dead_zone = 0.06

    def default_window(self):
        return {
            "x": 0.0,
            "y": 0.0,
            "w": 1.0,
            "h": 1.0,
            "zoom": 1.0
        }

    def center_window(self):
        return {
            "x": round((1.0 - self.fixed_width) / 2, 4),
            "y": 0.0,
            "w": self.fixed_width,
            "h": self.fixed_height,
            "zoom": round(1.0 / self.fixed_width, 2)
        }

    def clamp(self, value, minimum, maximum):
        return max(minimum, min(value, maximum))

    def clamp_window(self, window):
        w = self.fixed_width
        h = self.fixed_height

        x = self.clamp(float(window.get("x", 0.0)), 0.0, 1.0 - w)
        y = 0.0

        return {
            "x": round(x, 4),
            "y": y,
            "w": w,
            "h": h,
            "zoom": round(1.0 / w, 2)
        }

    def smooth(self, camera_id, target):
        previous = self.last_window.get(camera_id)

        if previous is None:
            result = self.clamp_window(target)
            self.last_window[camera_id] = result
            return result

        # Dead zone: kalau target dekat, jangan gerak
        if abs(target["x"] - previous["x"]) < self.dead_zone:
            return previous

        alpha = self.smoothing

        blended = {
            "x": previous["x"] + (target["x"] - previous["x"]) * alpha,
            "y": 0.0,
            "w": self.fixed_width,
            "h": self.fixed_height
        }

        result = self.clamp_window(blended)
        self.last_window[camera_id] = result

        return result

    def extract_focus_x(self, coordinates):
        if not coordinates or not coordinates.get("success"):
            return 0.5

        balls = coordinates.get("balls", [])
        players = coordinates.get("players", [])

        # Prioritas bola
        if balls:
            return float(balls[-1].get("court_x", 0.5))

        if players:
            xs = [
                float(p.get("court_x", 0.5))
                for p in players
                if p.get("court_x") is not None
            ]

            if xs:
                return sum(xs) / len(xs)

        return 0.5

    def decide_window(self, camera_id, director, coordinates=None):
        action = director.get("action")

        if action == "ZOOM_OUT":
            target = self.default_window()
            self.last_window[camera_id] = target
            return target

        focus_x = self.extract_focus_x(coordinates)

        # Taruh objek sedikit lebih ke tengah
        x = focus_x - (self.fixed_width / 2)

        target = {
            "x": x,
            "y": 0.0,
            "w": self.fixed_width,
            "h": self.fixed_height
        }

        return self.smooth(camera_id, self.clamp_window(target))

    def get_window(self, camera_id):
        return self.last_window.get(camera_id, self.center_window())
