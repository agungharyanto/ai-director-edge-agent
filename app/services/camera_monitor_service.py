import platform
import re
import subprocess

from app.repositories.camera_repository import CameraRepository
from app.repositories.event_repository import EventRepository


class CameraMonitorService:

    def ping_ip(self, ip_address):
        if not ip_address:
            return "DOWN", None

        system = platform.system().lower()

        if system == "windows":
            command = ["ping", "-n", "1", "-w", "1000", ip_address]
        else:
            command = ["ping", "-c", "1", "-W", "1", ip_address]

        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2
            )

            if result.returncode != 0:
                return "DOWN", None

            match = re.search(r"time[=<]([0-9.]+)", result.stdout)
            latency = float(match.group(1)) if match else None

            return "UP", latency

        except Exception:
            return "DOWN", None

    def check_all(self):
        repo = CameraRepository()
        event_repo = EventRepository()
        cameras = repo.all()

        results = []

        for camera in cameras:
            old_status = camera["ping_status"] or "UNKNOWN"
            new_status, latency = self.ping_ip(camera["ip_address"])

            repo.update_ping(camera["id"], new_status, latency)

            if old_status != new_status:
                level = "INFO" if new_status == "UP" else "WARNING"

                event_repo.create(
                    f"CAMERA_{new_status}",
                    level,
                    f"{camera['name']} ({camera['ip_address']}) berubah dari {old_status} ke {new_status}"
                )

            results.append({
                "id": camera["id"],
                "name": camera["name"],
                "ip_address": camera["ip_address"],
                "ping_status": new_status,
                "ping_latency_ms": latency
            })

        return results
