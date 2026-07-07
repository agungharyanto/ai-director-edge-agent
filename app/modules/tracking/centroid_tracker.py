import math


class CentroidTracker:

    def __init__(self, max_distance=120, max_missing=5):
        self.max_distance = max_distance
        self.max_missing = max_missing
        self.next_id = 1
        self.tracks = {}

    def _centroid(self, det):
        return (
            int((det["x1"] + det["x2"]) / 2),
            int((det["y1"] + det["y2"]) / 2)
        )

    def update(self, detections):
        assigned_tracks = set()
        assigned_detections = set()

        for det_idx, det in enumerate(detections):
            cx, cy = self._centroid(det)

            best_id = None
            best_distance = None

            for track_id, track in self.tracks.items():
                if track_id in assigned_tracks:
                    continue

                tx, ty = track["centroid"]
                distance = math.sqrt((cx - tx) ** 2 + (cy - ty) ** 2)

                if distance <= self.max_distance:
                    if best_distance is None or distance < best_distance:
                        best_distance = distance
                        best_id = track_id

            if best_id is not None:
                self.tracks[best_id] = {
                    "centroid": (cx, cy),
                    "missing": 0,
                    "detection": det
                }

                det["track_id"] = best_id
                assigned_tracks.add(best_id)
                assigned_detections.add(det_idx)

        for det_idx, det in enumerate(detections):
            if det_idx in assigned_detections:
                continue

            track_id = self.next_id
            self.next_id += 1

            cx, cy = self._centroid(det)

            self.tracks[track_id] = {
                "centroid": (cx, cy),
                "missing": 0,
                "detection": det
            }

            det["track_id"] = track_id

        for track_id in list(self.tracks.keys()):
            if track_id not in assigned_tracks:
                det = self.tracks[track_id].get("detection")
                still_visible = False

                if det:
                    for current in detections:
                        if current.get("track_id") == track_id:
                            still_visible = True
                            break

                if not still_visible:
                    self.tracks[track_id]["missing"] += 1

            if self.tracks[track_id]["missing"] > self.max_missing:
                self.tracks.pop(track_id, None)

        return detections
