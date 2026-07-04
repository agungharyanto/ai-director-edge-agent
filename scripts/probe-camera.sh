#!/bin/sh
set -u

CAMERA_NAME="${CAMERA_NAME:-padel-cam-01}"
PROBE_DIR="${PROBE_DIR:-/logs/probes}"
PROBE_OUTPUT="$PROBE_DIR/${CAMERA_NAME}_probe.txt"

mkdir -p "$PROBE_DIR"

echo "Probing camera: $CAMERA_NAME"
echo "RTSP URL: $RTSP_URL"

ffprobe \
  -hide_banner \
  -rtsp_transport tcp \
  -v error \
  -show_streams \
  -of default=noprint_wrappers=1 \
  "$RTSP_URL" > "$PROBE_OUTPUT"

echo "Probe result saved to $PROBE_OUTPUT"
cat "$PROBE_OUTPUT"
