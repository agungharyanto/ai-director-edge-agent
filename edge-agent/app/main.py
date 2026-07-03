import os
import subprocess
from datetime import datetime

camera_name = os.getenv("CAMERA_NAME", "padel-court-01")
rtsp_url = os.getenv("RTSP_URL")
record_seconds = os.getenv("RECORD_SECONDS", "30")

if not rtsp_url:
    raise Exception("RTSP_URL belum diset")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"/recordings/{camera_name}_{timestamp}.mp4"

cmd = [
    "ffmpeg",
    "-hide_banner",
    "-rtsp_transport", "tcp",
    "-i", rtsp_url,
    "-t", record_seconds,
    "-c:v", "copy",
    "-c:a", "aac",
    "-b:a", "128k",
    output_file
]

print("AI Director Edge Agent v0.1.0")
print(f"Camera: {camera_name}")
print(f"Output: {output_file}")
print("Starting recording with audio...")

subprocess.run(cmd, check=True)

print("Recording finished.")
