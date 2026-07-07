from cryptography.fernet import Fernet

from app.core.config import Config


class Crypto:

    def __init__(self):
        if not Config.MASTER_KEY:
            raise Exception("MASTER_KEY belum diset di .env")

        self.fernet = Fernet(Config.MASTER_KEY.encode())

    def encrypt(self, value):
        return self.fernet.encrypt(value.encode()).decode()

    def decrypt(self, value):
        return self.fernet.decrypt(value.encode()).decode()
