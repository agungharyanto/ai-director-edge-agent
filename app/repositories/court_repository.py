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
