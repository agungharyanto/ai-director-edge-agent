from app.core.config import Config
from app.core.database import Database
from app.core.logger import logger
from app.repositories.system_repository import SystemRepository

logger.info("Memulai AI Director Edge Agent")

db = Database()
db.initialize()

system = SystemRepository()
edge = system.bootstrap()

print()
print("======================================")
print(" AI Director Edge Agent")
print("======================================")
print("SITE     :", Config.SITE_ID)
print("EDGE     :", Config.EDGE_ID)
print("UUID     :", edge["uuid"])
print("HOSTNAME :", edge["hostname"])
print("DB       :", Config.DATABASE_PATH)
print("======================================")
