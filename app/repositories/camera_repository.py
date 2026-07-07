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

    def find(self, camera_id):
        return self.fetchone("SELECT * FROM camera WHERE id = ?", (camera_id,))

    def find_by_ip(self, ip_address):
        return self.fetchone(
            "SELECT * FROM camera WHERE ip_address = ? LIMIT 1",
            (ip_address,)
        )

    def by_court(self, court_uuid):
        return self.fetchall(
            """
            SELECT *
            FROM camera
            WHERE court_uuid = ?
            ORDER BY position, id
            """,
            (court_uuid,)
        )

    def count(self):
        row = self.fetchone("SELECT COUNT(*) AS total FROM camera")
        return row["total"]

    def count_by_status(self, status):
        row = self.fetchone(
            "SELECT COUNT(*) AS total FROM camera WHERE status = ?",
            (status,)
        )
        return row["total"]

    def count_by_ping_status(self, ping_status):
        row = self.fetchone(
            "SELECT COUNT(*) AS total FROM camera WHERE ping_status = ?",
            (ping_status,)
        )
        return row["total"]

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
                ping_status,
                provision_status
            )
            VALUES
            (
                ?,?,?,?,?,?,?,?,?,?
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
                "UNKNOWN",
                "UNKNOWN"
            )
        )

        return camera_uuid

    def update(self, camera_id, name, ip_address, rtsp_url, vendor, model, court_uuid=None):
        self.execute(
            """
            UPDATE camera
            SET name = ?,
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
            SET ping_status = ?,
                ping_latency_ms = ?,
                last_ping_at = datetime('now','localtime')
            WHERE id = ?
            """,
            (
                ping_status,
                ping_latency_ms,
                camera_id
            )
        )

    def assign_position(self, camera_id, court_uuid, position):
        self.execute(
            """
            UPDATE camera
            SET court_uuid = ?,
                position = ?,
                status = 'ASSIGNED'
            WHERE id = ?
            """,
            (
                court_uuid,
                position,
                camera_id
            )
        )

    def set_provision_status(self, camera_id, status, message=""):
        self.execute(
            """
            UPDATE camera
            SET provision_status = ?,
                provision_message = ?,
                provisioned_at = datetime('now','localtime')
            WHERE id = ?
            """,
            (
                status,
                message,
                camera_id
            )
        )

    def delete(self, camera_id):
        self.execute(
            "DELETE FROM camera WHERE id = ?",
            (camera_id,)
        )

def update_ai_ready(self, camera_id, ready):

    conn = self.connect()

    conn.execute(
        """
        UPDATE camera
        SET ai_ready=?
        WHERE id=?
        """,
        (
            1 if ready else 0,
            camera_id
        )
    )

    conn.commit()

    conn.close()
