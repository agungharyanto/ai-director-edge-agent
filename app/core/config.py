import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    APP_NAME = os.getenv("APP_NAME", "AI Director Edge Agent")
    APP_ENV = os.getenv("APP_ENV", "development")
    APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Asia/Jakarta")

    SITE_ID = os.getenv("SITE_ID", "site-001")
    EDGE_ID = os.getenv("EDGE_ID", "edge-001")

    WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
    WEB_PORT = int(os.getenv("WEB_PORT", "8080"))

    DATABASE_PATH = os.getenv(
        "DATABASE_PATH",
        "storage/database/edge.db"
    )

    SECRET_KEY = os.getenv("SECRET_KEY")


    HIKVISION_USERNAME = os.getenv("HIKVISION_USERNAME")
    HIKVISION_PASSWORD = os.getenv("HIKVISION_PASSWORD")


    MASTER_KEY = os.getenv("MASTER_KEY")
