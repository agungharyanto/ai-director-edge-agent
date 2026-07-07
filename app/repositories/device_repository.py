import uuid

from app.repositories.base_repository import BaseRepository


class DeviceRepository(BaseRepository):

    def all(self):
        return self.fetchall(
            """
            SELECT *
            FROM device_inventory
            ORDER BY id DESC
            """
        )

    def find_by_ip(self, ip_address):
        return self.fetchone(
            """
            SELECT *
            FROM device_inventory
            WHERE ip_address = ?
            LIMIT 1
            """,
            (ip_address,)
        )

    def upsert_from_discovery(
        self,
        ip_address,
        mac_address=None,
        hostname=None,
        vendor="Unknown",
        model="-",
        device_type="UNKNOWN",
        online_status="UNKNOWN",
        firmware=None,
        serial_number=None
    ):
        existing = self.find_by_ip(ip_address)

        if existing:
            self.execute(
                """
                UPDATE device_inventory
                SET
                    mac_address = COALESCE(?, mac_address),
                    hostname = COALESCE(?, hostname),
                    vendor = ?,
                    model = ?,
                    device_type = ?,
                    online_status = ?,
                    firmware = COALESCE(?, firmware),
                    serial_number = COALESCE(?, serial_number),
                    last_seen = datetime('now','localtime')
                WHERE id = ?
                """,
                (
                    mac_address,
                    hostname,
                    vendor,
                    model,
                    device_type,
                    online_status,
                    firmware,
                    serial_number,
                    existing["id"]
                )
            )

            return existing["uuid"]

        device_uuid = str(uuid.uuid4())

        self.execute(
            """
            INSERT INTO device_inventory
            (
                uuid,
                ip_address,
                mac_address,
                hostname,
                vendor,
                model,
                device_type,
                firmware,
                serial_number,
                status,
                online_status,
                adopted,
                first_seen,
                last_seen,
                created_at
            )
            VALUES
            (
                ?,?,?,?,?,?,?,?,?,?,?,0,datetime('now','localtime'),datetime('now','localtime'),datetime('now','localtime')
            )
            """,
            (
                device_uuid,
                ip_address,
                mac_address,
                hostname,
                vendor,
                model,
                device_type,
                firmware,
                serial_number,
                "DISCOVERED",
                online_status
            )
        )

        return device_uuid

    def count(self):
        row = self.fetchone("SELECT COUNT(*) AS total FROM device_inventory")
        return row["total"]

    def count_by_type(self, device_type):
        row = self.fetchone(
            """
            SELECT COUNT(*) AS total
            FROM device_inventory
            WHERE device_type = ?
            """,
            (device_type,)
        )
        return row["total"]

    def count_by_online_status(self, online_status):
        row = self.fetchone(
            """
            SELECT COUNT(*) AS total
            FROM device_inventory
            WHERE online_status = ?
            """,
            (online_status,)
        )
        return row["total"]
