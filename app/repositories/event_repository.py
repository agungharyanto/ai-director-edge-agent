from app.repositories.base_repository import BaseRepository


class EventRepository(BaseRepository):

    def all(
        self,
        limit=100,
        event_type=None,
        level=None,
        message=None,
        start_time=None,
        end_time=None
    ):
        query = "SELECT * FROM event_log WHERE 1=1"
        params = []

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)

        if level:
            query += " AND level = ?"
            params.append(level)

        if message:
            query += " AND message LIKE ?"
            params.append(f"%{message}%")

        if start_time:
            query += " AND created_at >= ?"
            params.append(start_time)

        if end_time:
            query += " AND created_at <= ?"
            params.append(end_time)

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        return self.fetchall(query, tuple(params))

    def count(self):
        row = self.fetchone("SELECT COUNT(*) AS total FROM event_log")
        return row["total"]

    def distinct_types(self):
        return self.fetchall(
            """
            SELECT DISTINCT event_type
            FROM event_log
            WHERE event_type IS NOT NULL
            ORDER BY event_type
            """
        )

    def distinct_levels(self):
        return self.fetchall(
            """
            SELECT DISTINCT level
            FROM event_log
            WHERE level IS NOT NULL
            ORDER BY level
            """
        )

    def create(self, event_type, level, message):
        self.execute(
            """
            INSERT INTO event_log
            (
                event_type,
                level,
                message,
                created_at
            )
            VALUES
            (
                ?,?,?,datetime('now','localtime')
            )
            """,
            (
                event_type,
                level,
                message
            )
        )

    def reset(self):
        self.execute("DELETE FROM event_log")
