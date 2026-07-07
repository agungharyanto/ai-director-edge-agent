from app.modules.credential.credential_engine import CredentialEngine
from app.modules.drivers.hikvision_driver import HikvisionDriver


class DriverManager:

    def detect(self, ip, ports):
        if 8000 in ports or 554 in ports:
            engine = CredentialEngine()
            credentials = engine.credentials_for_vendor("Hikvision")

            if not credentials:
                result = HikvisionDriver().probe(ip)

                if result:
                    return result

            for cred in credentials:
                result = HikvisionDriver().probe(
                    ip,
                    username=cred["username"],
                    password=cred["password"]
                )

                if result and result.get("success"):
                    engine.success(cred["id"])
                    result["credential_id"] = cred["id"]
                    return result

                engine.failed(cred["id"])

            result = HikvisionDriver().probe(ip)

            if result:
                return result

        return None
