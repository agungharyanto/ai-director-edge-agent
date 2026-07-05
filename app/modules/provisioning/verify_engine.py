import requests

from app.repositories.credential_repository import CredentialRepository
from app.modules.drivers.hikvision_driver import HikvisionDriver


class VerifyEngine:

    def verify(self, camera):
        result = {
            "credential": False,
            "snapshot": False,
            "rtsp": False,
            "osd_hidden": False,
            "overall": False,
            "message": ""
        }

        vendor = camera["vendor"]
        ip = camera["ip_address"]

        if vendor != "Hikvision":
            result["message"] = f"Vendor belum didukung: {vendor}"
            return result

        creds = CredentialRepository().active_by_vendor("Hikvision")

        if not creds:
            result["message"] = "Credential Hikvision belum tersedia"
            return result

        cred = creds[0]
        username = cred["username"]
        password = cred["password"]

        result["credential"] = True

        driver = HikvisionDriver()

        osd_status = driver.get_osd_status(
            ip,
            username,
            password
        )

        osd_ok = True

        for item in osd_status:
            if not item.get("success"):
                osd_ok = False

            if item.get("date_enabled") != "false":
                osd_ok = False

            if item.get("name_enabled") != "false":
                osd_ok = False

        result["osd_hidden"] = osd_ok

        rtsp_url = driver.rtsp(ip, username, password)
        result["rtsp"] = bool(rtsp_url)

        try:
            snapshot_url = driver.snapshot(ip, username, password)

            response = requests.get(
                snapshot_url,
                auth=requests.auth.HTTPDigestAuth(username, password),
                timeout=5,
                verify=False
            )

            result["snapshot"] = response.status_code == 200 and len(response.content) > 1000

        except Exception:
            result["snapshot"] = False

        result["overall"] = all([
            result["credential"],
            result["snapshot"],
            result["rtsp"],
            result["osd_hidden"]
        ])

        result["message"] = str({
            "osd_status": osd_status,
            "rtsp_url": rtsp_url
        })

        return result
