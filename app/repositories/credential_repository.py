from app.repositories.base_repository import BaseRepository
from app.modules.credential.crypto import Crypto


class CredentialRepository(BaseRepository):

    def all(self):
        return self.fetchall(
            """
            SELECT id,vendor,name,username,priority,enabled,success_count,failed_count,last_used,created_at
            FROM credential_profile
            ORDER BY vendor, priority ASC
            """
        )

    def create(self, vendor, name, username, password, priority=100, enabled=1):
        encrypted = Crypto().encrypt(password)

        self.execute(
            """
            INSERT INTO credential_profile
            (
                vendor,
                name,
                username,
                password_encrypted,
                priority,
                enabled
            )
            VALUES
            (
                ?,?,?,?,?,?
            )
            """,
            (
                vendor,
                name,
                username,
                encrypted,
                priority,
                enabled
            )
        )

    def active_by_vendor(self, vendor):
        rows = self.fetchall(
            """
            SELECT *
            FROM credential_profile
            WHERE enabled = 1
            AND vendor = ?
            ORDER BY priority ASC
            """,
            (vendor,)
        )

        result = []
        crypto = Crypto()

        for row in rows:
            result.append({
                "id": row["id"],
                "vendor": row["vendor"],
                "username": row["username"],
                "password": crypto.decrypt(row["password_encrypted"]),
                "priority": row["priority"]
            })

        return result

    def mark_success(self, credential_id):
        self.execute(
            """
            UPDATE credential_profile
            SET success_count = success_count + 1,
                last_used = datetime('now','localtime')
            WHERE id = ?
            """,
            (credential_id,)
        )

    def mark_failed(self, credential_id):
        self.execute(
            """
            UPDATE credential_profile
            SET failed_count = failed_count + 1,
                last_used = datetime('now','localtime')
            WHERE id = ?
            """,
            (credential_id,)
        )
