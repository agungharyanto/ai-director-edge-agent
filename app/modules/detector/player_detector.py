import cv2
from ultralytics import YOLO


class PlayerDetector:
    PERSON_CLASS_ID = 0

    def __init__(self, model_name="yolov8n.pt", confidence=0.35):
        self.model = YOLO(model_name)
        self.confidence = confidence
        try:
            self.model.fuse()
        except Exception:
            pass

    def detect(self, frame):
        results = self.model(
            frame,
            conf=self.confidence,
            verbose=False
        )

        detections = []

        for result in results:
            for box in result.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])

                if cls != self.PERSON_CLASS_ID:
                    continue

                x1, y1, x2, y2 = box.xyxy[0].tolist()

                detections.append({
                    "label": "player",
                    "confidence": round(conf, 3),
                    "x1": int(x1),
                    "y1": int(y1),
                    "x2": int(x2),
                    "y2": int(y2),
                    "width": int(x2 - x1),
                    "height": int(y2 - y1)
                })

        return detections

    def draw(self, frame, detections):
        output = frame.copy()

        for idx, det in enumerate(detections, start=1):
            x1 = det["x1"]
            y1 = det["y1"]
            x2 = det["x2"]
            y2 = det["y2"]

            player_id = det.get("track_id", idx)
            label = f"Player #{player_id} {det['confidence']}"

            cv2.rectangle(output, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                output,
                label,
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

        return output
