#!/bin/sh
set -eu

CAMERA_NAME="${CAMERA_NAME:-padel-cam-01}"
SEGMENT_SECONDS="${SEGMENT_SECONDS:-60}"
RECORDINGS_DIR="${RECORDINGS_DIR:-/recordings}"

OUT_DIR="$RECORDINGS_DIR/$CAMERA_NAME/incoming"
mkdir -p "$OUT_DIR"

echo "Starting recorder for $CAMERA_NAME"
echo "Segment duration: $SEGMENT_SECONDS seconds"
echo "Output dir: $OUT_DIR"

while true; do
  TS="$(date +"%Y%m%d_%H%M%S")"
  TMP_FILE="$OUT_DIR/${TS}.tmp.mp4"
  FINAL_FILE="$OUT_DIR/${TS}.mp4"

  ffmpeg \
    -hide_banner \
    -rtsp_transport tcp \
    -i "$RTSP_URL" \
    -t "$SEGMENT_SECONDS" \
    -map 0:v:0 \
    -map 0:a? \
    -c:v copy \
    -c:a aac \
    -b:a 128k \
    "$TMP_FILE"

  mv "$TMP_FILE" "$FINAL_FILE"
  /scripts/generate_metadata.sh "$FINAL_FILE"

  echo "Created: $FINAL_FILE"
done
