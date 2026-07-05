from app.repositories.device_repository import DeviceRepository


class InventorySync:

    def sync_discovery_result(self, result):
        repo = DeviceRepository()

        return repo.upsert_from_discovery(
            ip_address=result.get("ip_address"),
            mac_address=result.get("mac"),
            vendor=result.get("vendor", "Unknown"),
            model=result.get("model", "-"),
            device_type=result.get("device_type", "UNKNOWN"),
            online_status=result.get("ping_status") or result.get("ping") or "UNKNOWN",
            firmware=result.get("firmware"),
            serial_number=result.get("serial")
        )
