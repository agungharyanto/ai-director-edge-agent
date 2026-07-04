import sqlite3
from pathlib import Path

from app.core.config import Config
from app.core.logger import logger

class Database:

    def __init__(self):

        self.db_path = Path(Config.DATABASE_PATH)

        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.connection = sqlite3.connect(self.db_path)

        self.connection.row_factory = sqlite3.Row

    def initialize(self):

        schema = Path("app/database/schema.sql").read_text()

        self.connection.executescript(schema)

        self.connection.commit()

        logger.info("Database berhasil diinisialisasi.")

    def close(self):
        self.connection.close()
