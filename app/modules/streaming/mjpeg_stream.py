import cv2


class MJPEGStream:

    def __init__(self, rtsp_url):
        self.rtsp_url = rtsp_url

    def generate(self):

        cap = cv2.VideoCapture(self.rtsp_url)

        while True:

            ok, frame = cap.read()

            if not ok:
                break

            ok, jpg = cv2.imencode(".jpg", frame)

            if not ok:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + jpg.tobytes()
                + b"\r\n"
            )

        cap.release()
