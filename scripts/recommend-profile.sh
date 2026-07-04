#!/bin/sh
set -u

CAMERA_NAME="${CAMERA_NAME:-padel-cam-01}"
PROBE_DIR="${PROBE_DIR:-/logs/probes}"
PROBE_OUTPUT="$PROBE_DIR/${CAMERA_NAME}_probe.txt"
RECOMMENDATION_OUTPUT="$PROBE_DIR/${CAMERA_NAME}_recommendation.env"

if [ ! -f "$PROBE_OUTPUT" ]; then
  echo "Probe output not found: $PROBE_OUTPUT"
  echo "Run /scripts/probe-camera.sh first."
  exit 1
fi

VIDEO_CODEC="$(grep -B 20 -A 20 '^codec_type=video$' "$PROBE_OUTPUT" | grep -m1 '^codec_name=' | cut -d= -f2)"
AUDIO_CODEC="$(grep -B 20 -A 20 '^codec_type=audio$' "$PROBE_OUTPUT" | grep -m1 '^codec_name=' | cut -d= -f2)"

PROFILE="generic_rtsp_copy"

if [ "$AUDIO_CODEC" = "pcm_mulaw" ]; then
  PROFILE="hikvision_pcm_mulaw"
fi

if [ "$VIDEO_CODEC" = "hevc" ]; then
  PROFILE="rtsp_transcode_safe"
fi

echo "Detected video codec: ${VIDEO_CODEC:-unknown}"
echo "Detected audio codec: ${AUDIO_CODEC:-none}"
echo "Recommended profile: $PROFILE"

cat > "$RECOMMENDATION_OUTPUT" <<REC
CAMERA_PROFILE=$PROFILE
REC

echo "Recommendation saved to $RECOMMENDATION_OUTPUT"
