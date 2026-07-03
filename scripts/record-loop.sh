#!/usr/bin/env bash
set -euo pipefail

: "${RTSP_URL:?RTSP_URL is required}"
: "${CAMERA_NAME:?CAMERA_NAME is required}"
: "${SEGMENT_SECONDS:=60}"

echo "AI Director Edge Recorder started"
echo "Camera: ${CAMERA_NAME}"
echo "Segment seconds: ${SEGMENT_SECONDS}"

while true; do
  YEAR=$(date +%Y)
  MONTH=$(date +%m)
  DAY=$(date +%d)
  HOUR=$(date +%H)
  TS=$(date +%Y-%m-%d_%H-%M-%S)

  OUT_DIR="/recordings/${CAMERA_NAME}/${YEAR}/${MONTH}/${DAY}/${HOUR}"
  OUT_FILE="${OUT_DIR}/${TS}.mp4"

  mkdir -p "$OUT_DIR"

  echo "Recording to ${OUT_FILE}"

  ffmpeg \
    -hide_banner \
    -fflags +genpts \
    -use_wallclock_as_timestamps 1 \
    -rtsp_transport tcp \
    -i "$RTSP_URL" \
    -t "$SEGMENT_SECONDS" \
    -c:v copy \
    -c:a aac \
    -b:a 48k \
    -movflags +faststart \
    -y \
    "$OUT_FILE" || true

  sleep 1
done
