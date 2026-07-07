import cv2


class MotionDetector:

    def __init__(self):
        self.previous = None

    def detect(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.previous is None:
            self.previous = gray
            return frame, 0

        delta = cv2.absdiff(self.previous, gray)

        thresh = cv2.threshold(
            delta,
            25,
            255,
            cv2.THRESH_BINARY
        )[1]

        thresh = cv2.dilate(thresh, None, iterations=2)

        contours, _ = cv2.findContours(
            thresh,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        count = 0

        for c in contours:
            if cv2.contourArea(c) < 800:
                continue

            x, y, w, h = cv2.boundingRect(c)

            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                (0, 255, 0),
                2
            )

            count += 1

        self.previous = gray

        return frame, count
