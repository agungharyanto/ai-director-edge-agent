import cv2
import numpy as np


class BallDetector:

    def __init__(self):
        self.min_area = 8
        self.max_area = 500

    def detect(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        lower = np.array([25, 40, 80])
        upper = np.array([95, 255, 255])

        mask = cv2.inRange(hsv, lower, upper)

        mask = cv2.medianBlur(mask, 5)
        mask = cv2.erode(mask, None, iterations=1)
        mask = cv2.dilate(mask, None, iterations=2)

        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        detections = []

        for contour in contours:
            area = cv2.contourArea(contour)

            if area < self.min_area or area > self.max_area:
                continue

            x, y, w, h = cv2.boundingRect(contour)

            ratio = w / float(h) if h else 0

            if ratio < 0.5 or ratio > 2.0:
                continue

            detections.append({
                "label": "ball",
                "confidence": 0.5,
                "x1": int(x),
                "y1": int(y),
                "x2": int(x + w),
                "y2": int(y + h),
                "cx": int(x + w / 2),
                "cy": int(y + h / 2),
                "width": int(w),
                "height": int(h),
                "area": float(area)
            })

        detections = sorted(
            detections,
            key=lambda d: d["area"],
            reverse=True
        )

        return detections[:1]

    def draw(self, frame, detections):
        output = frame.copy()

        for det in detections:
            cx = det["cx"]
            cy = det["cy"]

            cv2.circle(output, (cx, cy), 10, (0, 255, 255), 2)
            cv2.circle(output, (cx, cy), 3, (0, 255, 255), -1)

            cv2.putText(
                output,
                "Ball",
                (cx + 12, max(cy - 12, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2
            )

        return output
