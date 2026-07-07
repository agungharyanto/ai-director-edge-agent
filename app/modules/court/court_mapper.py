import cv2
import numpy as np


class CourtMapper:

    def __init__(self):
        self.cache = {}

    def build_matrix(self, calibration):
        src = np.float32([
            [calibration["top_left_x"], calibration["top_left_y"]],
            [calibration["top_right_x"], calibration["top_right_y"]],
            [calibration["bottom_right_x"], calibration["bottom_right_y"]],
            [calibration["bottom_left_x"], calibration["bottom_left_y"]],
        ])

        dst = np.float32([
            [0.0, 0.0],
            [1.0, 0.0],
            [1.0, 1.0],
            [0.0, 1.0],
        ])

        return cv2.getPerspectiveTransform(src, dst)

    def map_point(self, calibration, x, y):
        matrix = self.build_matrix(calibration)

        point = np.float32([[[x, y]]])
        mapped = cv2.perspectiveTransform(point, matrix)[0][0]

        return {
            "x": round(float(mapped[0]), 4),
            "y": round(float(mapped[1]), 4)
        }

    def map_detection(self, calibration, detection):
        cx = detection.get("cx")
        cy = detection.get("cy")

        if cx is None or cy is None:
            cx = int((detection["x1"] + detection["x2"]) / 2)
            cy = int(detection["y2"])

        court = self.map_point(calibration, cx, cy)

        result = dict(detection)
        result["court_x"] = court["x"]
        result["court_y"] = court["y"]

        return result
