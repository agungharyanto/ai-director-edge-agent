#!/bin/sh
set -u

CONFIG_FILE="${DISCOVERY_CONFIG:-/config/discovery/discovery.env}"

if [ -f "$CONFIG_FILE" ]; then
  . "$CONFIG_FILE"
fi

DISCOVERY_DIR="${DISCOVERY_DIR:-/logs/discovery}"
OUTPUT="${DISCOVERY_OUTPUT:-$DISCOVERY_DIR/devices.json}"

SUBNET="${DISCOVERY_SUBNET:-192.168.1}"
START="${DISCOVERY_START:-1}"
END="${DISCOVERY_END:-254}"
PORTS="${DISCOVERY_PORTS:-80 554 8000 8080 8899}"
TIMEOUT="${DISCOVERY_TIMEOUT:-1}"
REQUIRE_PING="${DISCOVERY_REQUIRE_PING:-true}"

mkdir -p "$DISCOVERY_DIR"

echo "Scanning subnet: $SUBNET.$START-$END"
echo "Ports: $PORTS"
echo "Require ping: $REQUIRE_PING"
echo "Output: $OUTPUT"

echo "[" > "$OUTPUT"
FIRST=1

for i in $(seq "$START" "$END"); do
  IP="$SUBNET.$i"

  if [ "$REQUIRE_PING" = "true" ]; then
    if ! ping -c 1 -W 1 "$IP" >/dev/null 2>&1; then
      continue
    fi
  fi

  OPEN_PORTS=""

  for PORT in $PORTS; do
    if nc -z -w "$TIMEOUT" "$IP" "$PORT" 2>/dev/null; then
      OPEN_PORTS="$OPEN_PORTS $PORT"
    fi
  done

  if [ -n "$OPEN_PORTS" ]; then
    RTSP=false
    HTTP=false
    ONVIF=false
    CONFIDENCE=20

    echo "$OPEN_PORTS" | grep -q "554" && RTSP=true && CONFIDENCE=$((CONFIDENCE + 35))
    echo "$OPEN_PORTS" | grep -q "80" && HTTP=true && CONFIDENCE=$((CONFIDENCE + 20))
    echo "$OPEN_PORTS" | grep -q "8000" && ONVIF=true && CONFIDENCE=$((CONFIDENCE + 25))

    [ "$CONFIDENCE" -gt 100 ] && CONFIDENCE=100

    if [ "$FIRST" -eq 0 ]; then
      echo "," >> "$OUTPUT"
    fi

    cat >> "$OUTPUT" <<JSON
  {
    "ip": "$IP",
    "open_ports": "$OPEN_PORTS",
    "rtsp_candidate": $RTSP,
    "http_candidate": $HTTP,
    "onvif_candidate": $ONVIF,
    "confidence": $CONFIDENCE,
    "status": "candidate"
  }
JSON

    FIRST=0
    echo "Found: $IP ports:$OPEN_PORTS confidence:$CONFIDENCE"
  fi
done

echo "" >> "$OUTPUT"
echo "]" >> "$OUTPUT"

echo "Discovery result saved to $OUTPUT"
cat "$OUTPUT"
