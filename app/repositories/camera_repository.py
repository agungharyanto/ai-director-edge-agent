import uuid

from app.repositories.base_repository import BaseRepository


class CameraRepository(BaseRepository):

    def all(self):
        return self.fetchall(
            """
            SELECT
                camera.*,
                court.name AS court_name
            FROM camera
            LEFT JOIN court
                ON camera.court_uuid = court.uuid
            ORDER BY camera.id
            """
        )

    def count(self):
        row = self.fetchone("SELECT COUNT(*) AS total FROM camera")
        return row["total"]

    def count_by_status(self, status):
        row = self.fetchone(
            """
            SELECT COUNT(*) AS total
            FROM camera
            WHERE status = ?
            """,
            (status,)
        )
        return row["total"]


    def count_by_ping_status(self, ping_status):
        row = self.fetchone(
            """
            SELECT COUNT(*) AS total
            FROM camera
            WHERE ping_status = ?
            """,
            (ping_status,)
        )
        return row["total"]

    def find(self, camera_id):
        return self.fetchone(
            """
            SELECT *
            FROM camera
            WHERE id = ?
            """,
            (camera_id,)
        )

    def create(self, name, ip_address, rtsp_url, vendor, model, court_uuid=None):
        camera_uuid = str(uuid.uuid4())

        self.execute(
            """
            INSERT INTO camera
            (
                uuid,
                court_uuid,
                name,
                ip_address,
                rtsp_url,
                vendor,
                model,
                status,
                ping_status
            )
            VALUES
            (
                ?,?,?,?,?,?,?,?,?
            )
            """,
            (
                camera_uuid,
                court_uuid,
                name,
                ip_address,
                rtsp_url,
                vendor,
                model,
                "ASSIGNED" if court_uuid else "NEW",
                "UNKNOWN"
            )
        )

        return camera_uuid

    def update(self, camera_id, name, ip_address, rtsp_url, vendor, model, court_uuid=None):
        self.execute(
            """
            UPDATE camera
            SET
                name = ?,
                ip_address = ?,
                rtsp_url = ?,
                vendor = ?,
                model = ?,
                court_uuid = ?,
                status = ?
            WHERE id = ?
            """,
            (
                name,
                ip_address,
                rtsp_url,
                vendor,
                model,
                court_uuid,
                "ASSIGNED" if court_uuid else "NEW",
                camera_id
            )
        )

    def update_ping(self, camera_id, ping_status, ping_latency_ms):
        self.execute(
            """
            UPDATE camera
            SET
                ping_status = ?,
                ping_latency_ms = ?,
                last_ping_at = datetime('now', 'localtime')
            WHERE id = ?
            """,
            (
                ping_status,
                ping_latency_ms,
                camera_id
            )
        )

    def delete(self, camera_id):
        self.execute(
            """
            DELETE FROM camera
            WHERE id = ?
            """,
            (camera_id,)
        )
