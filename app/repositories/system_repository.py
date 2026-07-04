import socket
import uuid

from app.core.config import Config
from app.repositories.base_repository import BaseRepository


class SystemRepository(BaseRepository):

    def bootstrap(self):

        row = self.fetchone(
            "SELECT * FROM edge_identity LIMIT 1"
        )

        if row:
            return row

        edge_uuid = str(uuid.uuid4())

        self.execute(
            """
            INSERT INTO edge_identity
            (
                uuid,
                site_id,
                edge_id,
                hostname,
                app_version
            )
            VALUES
            (
                ?,?,?,?,?
            )
            """,
            (
                edge_uuid,
                Config.SITE_ID,
                Config.EDGE_ID,
                socket.gethostname(),
                "0.4.0"
            )
        )

        return self.fetchone(
            "SELECT * FROM edge_identity LIMIT 1"
        )
