import uuid

from app.repositories.base_repository import BaseRepository


class CourtRepository(BaseRepository):

    def all(self):
        return self.fetchall(
            """
            SELECT *
            FROM court
            ORDER BY id
            """
        )

    def find(self, court_id):
        return self.fetchone(
            """
            SELECT *
            FROM court
            WHERE id = ?
            """,
            (court_id,)
        )

    def count(self):
        row = self.fetchone("SELECT COUNT(*) AS total FROM court")
        return row["total"]

    def create(self, name, description=""):
        court_uuid = str(uuid.uuid4())

        self.execute(
            """
            INSERT INTO court
            (
                uuid,
                name,
                description,
                status
            )
            VALUES
            (
                ?,?,?,?
            )
            """,
            (
                court_uuid,
                name,
                description,
                "ACTIVE"
            )
        )

        return court_uuid

    def get_camera_calibration(self, camera_id):
        return self.fetchone(
            """
            SELECT *
            FROM camera_calibration
            WHERE camera_id = ?
            """,
            (camera_id,)
        )

    def save_camera_calibration(self, camera_id, points):
        self.execute(
            """
            INSERT INTO camera_calibration
            (
                camera_id,
                top_left_x,
                top_left_y,
                top_right_x,
                top_right_y,
                bottom_right_x,
                bottom_right_y,
                bottom_left_x,
                bottom_left_y,
                updated_at
            )
            VALUES
            (
                ?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP
            )
            ON CONFLICT(camera_id) DO UPDATE SET
                top_left_x = excluded.top_left_x,
                top_left_y = excluded.top_left_y,
                top_right_x = excluded.top_right_x,
                top_right_y = excluded.top_right_y,
                bottom_right_x = excluded.bottom_right_x,
                bottom_right_y = excluded.bottom_right_y,
                bottom_left_x = excluded.bottom_left_x,
                bottom_left_y = excluded.bottom_left_y,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                camera_id,
                points["top_left"][0],
                points["top_left"][1],
                points["top_right"][0],
                points["top_right"][1],
                points["bottom_right"][0],
                points["bottom_right"][1],
                points["bottom_left"][0],
                points["bottom_left"][1],
            )
        )
