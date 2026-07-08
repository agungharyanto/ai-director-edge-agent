import os

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
    "rtsp_transport;tcp|"
    "stimeout;5000000|"
    "max_delay;500000|"
    "buffer_size;1048576"
)

import cv2
import argparse
from flask import Flask, Response
from ultralytics import YOLO

from app.modules.tracking.smooth_director import SmoothDirector, Box


app = Flask(__name__)

model = None
cap = None
director = None
args = None

frame_w = 0
frame_h = 0


def open_camera():
    global cap, director, frame_w, frame_h

    if cap is not None:
        cap.release()

    cap = cv2.VideoCapture(args.source, cv2.CAP_FFMPEG)

    if not cap.isOpened():
        raise RuntimeError("Gagal membuka RTSP camera")

    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"Camera opened: {frame_w}x{frame_h}")

    director = SmoothDirector(
        frame_w=frame_w,
        frame_h=frame_h,
        min_zoom=1.0,
        max_zoom=2.6,
        target_fill=0.68,
        deadzone_px=55,
        zoom_deadzone=0.07,
        pan_speed=0.065,
        zoom_speed=0.018,
        prediction_strength=0.45,
    )


def generate_frames():
    global cap, director

    failed_reads = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            failed_reads += 1
            print(f"Frame gagal dibaca: {failed_reads}")

            if failed_reads <= 20:
                try:
                    open_camera()
                    continue
                except Exception as e:
                    print(f"Reconnect gagal: {e}")
                    continue

            break

        failed_reads = 0

        results = model(frame, conf=args.conf, verbose=False)[0]

        player_boxes = []

        for r in results.boxes:
            cls_id = int(r.cls[0])
            label = model.names[cls_id]

            if label != "person":
                continue

            x1, y1, x2, y2 = r.xyxy[0].tolist()

            player_boxes.append(
                Box(
                    x1=float(x1),
                    y1=float(y1),
                    x2=float(x2),
                    y2=float(y2),
                )
            )

        crop_x1, crop_y1, crop_x2, crop_y2 = director.update(player_boxes)

        cropped = frame[crop_y1:crop_y2, crop_x1:crop_x2]

        if cropped.size == 0:
            output = frame
        else:
            output = cv2.resize(cropped, (frame_w, frame_h))

        cv2.putText(
            output,
            f"AI Director v0.4.57 | Players: {len(player_boxes)}",
            (30, 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

        ok, buffer = cv2.imencode(".jpg", output, [cv2.IMWRITE_JPEG_QUALITY, 80])

        if not ok:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            buffer.tobytes() +
            b"\r\n"
        )


@app.route("/")
def index():
    return """
    <html>
      <head>
        <title>AI Director v0.4.57 Live</title>
        <style>
          body {
            background: #111;
            color: white;
            font-family: Arial;
            text-align: center;
          }
          img {
            width: 95vw;
            max-width: 1400px;
            border-radius: 12px;
            border: 2px solid #333;
          }
        </style>
      </head>
      <body>
        <h2>AI Director v0.4.57 Live Preview</h2>
        <img src="/stream">
      </body>
    </html>
    """


@app.route("/stream")
def stream():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--model", default="yolov8n.pt")
    parser.add_argument("--conf", type=float, default=0.35)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8090)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    print("Loading YOLO...")
    model = YOLO(args.model)

    open_camera()

    print(f"Open browser: http://localhost:{args.port}")
    app.run(host=args.host, port=args.port, threaded=True)
