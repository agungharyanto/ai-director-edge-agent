import psutil

from app.repositories.health_repository import HealthRepository


class HealthService:

    def collect(self):
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent

        repo = HealthRepository()
        repo.create(cpu, ram, disk)

        return {
            "cpu": cpu,
            "ram": ram,
            "disk": disk,
            "temperature": None
        }
