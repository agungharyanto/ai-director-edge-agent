from app.repositories.base_repository import BaseRepository


class HealthRepository(BaseRepository):

    def latest(self):
        return self.fetchone(
            """
            SELECT *
            FROM health
            ORDER BY id DESC
            LIMIT 1
            """
        )

    def history(self, limit=30):
        return self.fetchall(
            """
            SELECT *
            FROM health
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        )

    def create(self, cpu, ram, disk, temperature=None):
        self.execute(
            """
            INSERT INTO health
            (
                cpu,
                ram,
                disk,
                temperature,
                created_at
            )
            VALUES
            (
                ?,?,?,?,datetime('now','localtime')
            )
            """,
            (
                cpu,
                ram,
                disk,
                temperature
            )
        )
