#!/bin/sh
set -u

CAMERA_NAME="${CAMERA_NAME:-padel-cam-01}"
SEGMENT_SECONDS="${SEGMENT_SECONDS:-60}"
RECORDINGS_DIR="${RECORDINGS_DIR:-/recordings}"
CAMERA_PROFILE="${CAMERA_PROFILE:-rtsp_transcode_safe}"
PROFILE_FILE="/config/camera-profiles/${CAMERA_PROFILE}.env"

if [ -f "$PROFILE_FILE" ]; then
  . "$PROFILE_FILE"
else
  echo "Profile not found: $PROFILE_FILE"
  exit 1
fi

OUT_DIR="$RECORDINGS_DIR/$CAMERA_NAME/incoming"
mkdir -p "$OUT_DIR"

echo "Starting recorder for $CAMERA_NAME"
echo "Camera profile: $CAMERA_PROFILE"
echo "Segment duration: $SEGMENT_SECONDS seconds"
echo "Output dir: $OUT_DIR"

while true; do
  TS="$(date +"%Y%m%d_%H%M%S")"
  TMP_FILE="$OUT_DIR/${TS}.tmp.mp4"
  FINAL_FILE="$OUT_DIR/${TS}.mp4"

  rm -f "$TMP_FILE"

  if [ "${VIDEO_MODE:-copy}" = "copy" ]; then
    VIDEO_ARGS="-c:v copy"
  else
    VIDEO_ARGS="-r ${VIDEO_FPS:-20} -fps_mode cfr -c:v ${VIDEO_CODEC:-libx264} -preset ${VIDEO_PRESET:-veryfast} -crf ${VIDEO_CRF:-23}"
  fi

  if [ "${FFMPEG_TIMESTAMP_MODE:-genpts}" = "wallclock" ]; then
    TS_ARGS="-fflags +genpts -use_wallclock_as_timestamps 1"
  else
    TS_ARGS="-fflags +genpts"
  fi

  echo "Recording segment: $FINAL_FILE"

  if ffmpeg -hide_banner -rtsp_transport tcp $TS_ARGS \
    -i "$RTSP_URL" \
    -t "$SEGMENT_SECONDS" \
    -map 0:v:0 \
    -map 0:a? \
    $VIDEO_ARGS \
    -c:a aac \
    -b:a "${AUDIO_BITRATE:-48k}" \
    -movflags +faststart \
    "$TMP_FILE"; then

    if [ -s "$TMP_FILE" ]; then
      mv "$TMP_FILE" "$FINAL_FILE"
      /scripts/generate_metadata.sh "$FINAL_FILE"
      echo "Created: $FINAL_FILE"
    else
      echo "TMP file is empty, removing..."
      rm -f "$TMP_FILE"
    fi

  else
    echo "FFmpeg failed, retrying in 5 seconds..."
    rm -f "$TMP_FILE"
    sleep 5
  fi
done
