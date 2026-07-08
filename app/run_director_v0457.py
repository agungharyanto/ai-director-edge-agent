import cv2
import argparse
from ultralytics import YOLO

from app.modules.tracking.smooth_director import SmoothDirector, Box


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="Path video atau RTSP URL")
    parser.add_argument("--output", default="output_v0457.mp4")
    parser.add_argument("--model", default="yolov8n.pt")
    parser.add_argument("--conf", type=float, default=0.35)
    parser.add_argument("--show", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()

    print("AI Director v0.4.57 starting...")
    print(f"Source: {args.source}")

    model = YOLO(args.model)

    cap = cv2.VideoCapture(args.source)

    if not cap.isOpened():
        raise RuntimeError("Gagal membuka source video / RTSP")

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps <= 0 or fps > 120:
        fps = 25

    print(f"Frame: {frame_width}x{frame_height} @ {fps} FPS")

    director = SmoothDirector(
        frame_w=frame_width,
        frame_h=frame_height,
        min_zoom=1.0,
        max_zoom=2.6,
        target_fill=0.68,
        deadzone_px=55,
        zoom_deadzone=0.07,
        pan_speed=0.065,
        zoom_speed=0.018,
        prediction_strength=0.45,
    )

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(
        args.output,
        fourcc,
        fps,
        (frame_width, frame_height),
    )

    frame_count = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            break

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
            output = cv2.resize(cropped, (frame_width, frame_height))

        writer.write(output)

        frame_count += 1

        if frame_count % 50 == 0:
            print(f"Processed frame: {frame_count}")

        if args.show:
            preview = output.copy()

            cv2.putText(
                preview,
                f"Players: {len(player_boxes)}",
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )

            cv2.imshow("AI Director v0.4.57", preview)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    writer.release()
    cv2.destroyAllWindows()

    print("Done.")
    print(f"Output saved: {args.output}")


if __name__ == "__main__":
    main()
