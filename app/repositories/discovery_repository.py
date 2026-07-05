from app.repositories.base_repository import BaseRepository


class DiscoveryRepository(BaseRepository):

    def create_job(self, network, total_hosts):
        cursor = self.execute(
            """
            INSERT INTO discovery_job
            (
                network,
                status,
                total_hosts,
                scanned_hosts,
                found_hosts,
                started_at
            )
            VALUES
            (
                ?,?,?,?,?,datetime('now','localtime')
            )
            """,
            (
                network,
                "RUNNING",
                total_hosts,
                0,
                0
            )
        )

        return cursor.lastrowid

    def update_progress(self, job_id, scanned_hosts, found_hosts):
        self.execute(
            """
            UPDATE discovery_job
            SET scanned_hosts = ?, found_hosts = ?
            WHERE id = ?
            """,
            (
                scanned_hosts,
                found_hosts,
                job_id
            )
        )

    def finish_job(self, job_id):
        self.execute(
            """
            UPDATE discovery_job
            SET status = 'DONE', finished_at = datetime('now','localtime')
            WHERE id = ?
            """,
            (job_id,)
        )

    def get_job(self, job_id):
        return self.fetchone(
            """
            SELECT *
            FROM discovery_job
            WHERE id = ?
            """,
            (job_id,)
        )

    def latest_job(self):
        return self.fetchone(
            """
            SELECT *
            FROM discovery_job
            ORDER BY id DESC
            LIMIT 1
            """
        )

    def add_result(self, job_id, ip_address, ping_status, open_ports, vendor="Unknown", model="-", confidence=0):
        self.execute(
            """
            INSERT INTO discovery_result
            (
                job_id,
                ip_address,
                ping_status,
                open_ports,
                vendor,
                model,
                confidence,
                created_at
            )
            VALUES
            (
                ?,?,?,?,?,?,?,datetime('now','localtime')
            )
            """,
            (
                job_id,
                ip_address,
                ping_status,
                ",".join(str(port) for port in open_ports),
                vendor,
                model,
                confidence
            )
        )

    def results(self, job_id):
        return self.fetchall(
            """
            SELECT *
            FROM discovery_result
            WHERE job_id = ?
            ORDER BY id ASC
            """,
            (job_id,)
        )
