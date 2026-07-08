import cv2


class CropEngine:

    def crop(self, frame, window, output_width=960):
        if frame is None:
            return None

        h, w = frame.shape[:2]

        x = max(0.0, min(float(window.get("x", 0.0)), 1.0))
        y = max(0.0, min(float(window.get("y", 0.0)), 1.0))
        ww = max(0.1, min(float(window.get("w", 1.0)), 1.0))
        hh = max(0.1, min(float(window.get("h", 1.0)), 1.0))

        x1 = int(x * w)
        y1 = int(y * h)
        x2 = int((x + ww) * w)
        y2 = int((y + hh) * h)

        x2 = min(x2, w)
        y2 = min(y2, h)

        if x2 <= x1 or y2 <= y1:
            return frame

        cropped = frame[y1:y2, x1:x2]

        ch, cw = cropped.shape[:2]
        ratio = output_width / float(cw)
        output_height = int(ch * ratio)

        return cv2.resize(cropped, (output_width, output_height))
