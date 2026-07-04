#!/bin/sh
set -eu

VIDEO_FILE="$1"
CAMERA_NAME="${CAMERA_NAME:-padel-cam-01}"
SEGMENT_SECONDS="${SEGMENT_SECONDS:-60}"

JSON_FILE="${VIDEO_FILE%.*}.json"
FILENAME="$(basename "$VIDEO_FILE")"
SIZE="$(stat -c%s "$VIDEO_FILE")"
CREATED_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

cat > "$JSON_FILE" <<JSON
{
  "camera": "$CAMERA_NAME",
  "filename": "$FILENAME",
  "duration": $SEGMENT_SECONDS,
  "size": $SIZE,
  "status": "incoming",
  "created_at": "$CREATED_AT"
}
JSON
