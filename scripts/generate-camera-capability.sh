#!/bin/sh
set -u

CAMERA_NAME="${CAMERA_NAME:-padel-cam-01}"
PROBE_DIR="${PROBE_DIR:-/logs/probes}"
CAPABILITY_DIR="${CAPABILITY_DIR:-/logs/capabilities}"

PROBE_OUTPUT="$PROBE_DIR/${CAMERA_NAME}_probe.txt"
RECOMMENDATION_OUTPUT="$PROBE_DIR/${CAMERA_NAME}_recommendation.env"
CAPABILITY_OUTPUT="$CAPABILITY_DIR/${CAMERA_NAME}.json"

mkdir -p "$CAPABILITY_DIR"

if [ ! -f "$PROBE_OUTPUT" ]; then
  echo "Probe output not found: $PROBE_OUTPUT"
  exit 1
fi

VIDEO_CODEC="$(grep -B 20 -A 20 '^codec_type=video$' "$PROBE_OUTPUT" | grep -m1 '^codec_name=' | cut -d= -f2)"
AUDIO_CODEC="$(grep -B 20 -A 20 '^codec_type=audio$' "$PROBE_OUTPUT" | grep -m1 '^codec_name=' | cut -d= -f2)"
WIDTH="$(grep -m1 '^width=' "$PROBE_OUTPUT" | cut -d= -f2)"
HEIGHT="$(grep -m1 '^height=' "$PROBE_OUTPUT" | cut -d= -f2)"
FPS="$(grep -m1 '^avg_frame_rate=' "$PROBE_OUTPUT" | cut -d= -f2)"
TIME_BASE="$(grep -m1 '^time_base=' "$PROBE_OUTPUT" | cut -d= -f2)"

RECOMMENDED_PROFILE="unknown"
if [ -f "$RECOMMENDATION_OUTPUT" ]; then
  RECOMMENDED_PROFILE="$(grep '^CAMERA_PROFILE=' "$RECOMMENDATION_OUTPUT" | cut -d= -f2)"
fi

cat > "$CAPABILITY_OUTPUT" <<JSON
{
  "camera_name": "$CAMERA_NAME",
  "source": "rtsp",
  "video": {
    "codec": "$VIDEO_CODEC",
    "width": "$WIDTH",
    "height": "$HEIGHT",
    "fps": "$FPS",
    "time_base": "$TIME_BASE"
  },
  "audio": {
    "codec": "${AUDIO_CODEC:-none}"
  },
  "recommended_profile": "$RECOMMENDED_PROFILE"
}
JSON

echo "Camera capability saved to $CAPABILITY_OUTPUT"
cat "$CAPABILITY_OUTPUT"
