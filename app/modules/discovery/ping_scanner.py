import platform
import subprocess


class PingScanner:

    def ping(self, ip_address):
        system = platform.system().lower()

        if system == "windows":
            command = ["ping", "-n", "1", "-w", "500", ip_address]
        else:
            command = ["ping", "-c", "1", "-W", "1", ip_address]

        try:
            result = subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2
            )

            return result.returncode == 0

        except Exception:
            return False
