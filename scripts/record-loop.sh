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

  rm -f "$TMP_FILE"

  ffmpeg \
    -hide_banner \
    -rtsp_transport tcp \
    -fflags +genpts \
    -use_wallclock_as_timestamps 1 \
    -i "$RTSP_URL" \
    -t "$SEGMENT_SECONDS" \
    -map 0:v:0 \
    -map 0:a? \
    -r 20 \
    -fps_mode cfr \
    -c:v libx264 \
    -preset veryfast \
    -crf 23 \
    -c:a aac \
    -b:a 48k \
    -movflags +faststart \
    "$TMP_FILE"

  mv "$TMP_FILE" "$FINAL_FILE"
  /scripts/generate_metadata.sh "$FINAL_FILE"

  echo "Created: $FINAL_FILE"
done
