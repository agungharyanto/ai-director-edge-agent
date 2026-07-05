import time
import requests
import urllib3
import xml.etree.ElementTree as ET

from app.modules.drivers.base_driver import BaseDriver
from app.modules.xml.xml_config_engine import XMLConfigEngine

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HikvisionDriver(BaseDriver):

    def _auth(self, username=None, password=None):
        if username and password:
            return requests.auth.HTTPDigestAuth(username, password)
        return None

    def probe(self, ip, username=None, password=None):
        return self.device_info(ip, username, password)

    def device_info(self, ip, username=None, password=None):
        urls = [
            f"http://{ip}/ISAPI/System/deviceInfo",
            f"https://{ip}/ISAPI/System/deviceInfo"
        ]

        auth = self._auth(username, password)

        for url in urls:
            try:
                r = requests.get(url, timeout=3, verify=False, auth=auth)

                if r.status_code == 401:
                    return {
                        "vendor": "Hikvision",
                        "success": False,
                        "auth_required": True,
                        "status_code": 401,
                        "message": "Hikvision terdeteksi, tapi butuh username/password"
                    }

                if r.status_code != 200:
                    continue

                root = ET.fromstring(r.text)
                data = {}

                for item in root:
                    tag = item.tag.split("}")[-1]
                    data[tag] = item.text

                return {
                    "vendor": "Hikvision",
                    "success": True,
                    "auth_required": False,
                    "status_code": 200,
                    "model": data.get("model"),
                    "firmware": data.get("firmwareVersion"),
                    "serial": data.get("serialNumber"),
                    "mac": data.get("macAddress"),
                    "device_name": data.get("deviceName"),
                    "device_id": data.get("deviceID")
                }

            except Exception:
                continue

        return None

    def capability(self, ip, username=None, password=None):
        return {
            "rtsp": True,
            "snapshot": True,
            "isapi": True,
            "onvif": None,
            "audio": None,
            "ptz": None
        }

    def snapshot(self, ip, username=None, password=None):
        return f"http://{ip}/ISAPI/Streaming/channels/101/picture"

    def rtsp(self, ip, username=None, password=None):
        if username and password:
            return f"rtsp://{username}:{password}@{ip}:554/Streaming/Channels/101"
        return f"rtsp://{ip}:554/Streaming/Channels/101"

    def health(self, ip, username=None, password=None):
        return {}

    def configure(self, ip, username=None, password=None):
        return False

    def _osd_urls(self, ip):
        return [
            f"http://{ip}/ISAPI/System/Video/inputs/channels/1/overlays",
            f"http://{ip}/ISAPI/System/Video/inputs/channels/101/overlays",
            f"http://{ip}/ISAPI/System/Video/inputs/channels/102/overlays",
        ]

    def _apply_osd(self, ip, username, password, enabled, name_value=None):
        auth = self._auth(username, password)
        xml = XMLConfigEngine(auth)

        results = []

        for url in self._osd_urls(ip):
            current = xml.get_text(url)

            if not current.get("success"):
                results.append({
                    "url": url,
                    "success": False,
                    "stage": "GET",
                    "status_code": current.get("status_code"),
                    "message": current.get("error", "GET gagal")
                })
                continue

            xml_text = current["text"]

            xml_text = xml.set_tag_value_inside_block(
                xml_text,
                "DateTimeOverlay",
                "enabled",
                "true" if enabled else "false"
            )

            xml_text = xml.set_tag_value_inside_block(
                xml_text,
                "DateTimeOverlay",
                "displayWeek",
                "true" if enabled else "false"
            )

            xml_text = xml.set_tag_value_inside_block(
                xml_text,
                "channelNameOverlay",
                "enabled",
                "true" if enabled else "false"
            )

            if name_value is not None:
                xml_text = xml.set_tag_value_inside_block(
                    xml_text,
                    "channelNameOverlay",
                    "name",
                    name_value
                )

            put_result = xml.put_text(url, xml_text)

            verify = xml.get_text(url)
            verify_text = verify.get("text", "")

            results.append({
                "url": url,
                "success": put_result.get("success", False),
                "stage": "PUT",
                "status_code": put_result.get("status_code"),
                "date_enabled": xml.get_tag_value_inside_block(
                    verify_text,
                    "DateTimeOverlay",
                    "enabled"
                ),
                "name_enabled": xml.get_tag_value_inside_block(
                    verify_text,
                    "channelNameOverlay",
                    "enabled"
                ),
                "name": xml.get_tag_value_inside_block(
                    verify_text,
                    "channelNameOverlay",
                    "name"
                ),
                "response": put_result.get("response", "")
            })

        ok = any(item.get("success") for item in results)

        return {
            "success": ok,
            "results": results
        }

    def reboot(self, ip, username=None, password=None):
        auth = self._auth(username, password)
        url = f"http://{ip}/ISAPI/System/reboot"

        try:
            r = requests.put(
                url,
                auth=auth,
                verify=False,
                timeout=5
            )

            return {
                "success": r.status_code in [200, 201],
                "status_code": r.status_code,
                "response": r.text[:500]
            }

        except Exception as error:
            return {
                "success": False,
                "error": str(error)
            }

    def hide_osd(self, ip, username=None, password=None):
        osd_result = self._apply_osd(
            ip=ip,
            username=username,
            password=password,
            enabled=False,
            name_value=""
        )

        reboot_result = self.reboot(ip, username, password)

        osd_result["reboot"] = reboot_result
        osd_result["note"] = "OSD dimatikan dan kamera reboot otomatis. Tunggu 60-120 detik."

        return osd_result

    def show_osd(self, ip, username=None, password=None):
        osd_result = self._apply_osd(
            ip=ip,
            username=username,
            password=password,
            enabled=True,
            name_value="AI Director Debug"
        )

        reboot_result = self.reboot(ip, username, password)

        osd_result["reboot"] = reboot_result
        osd_result["note"] = "OSD debug dinyalakan dan kamera reboot otomatis. Tunggu 60-120 detik."

        return osd_result

    def get_osd_status(self, ip, username=None, password=None):
        auth = self._auth(username, password)
        xml = XMLConfigEngine(auth)

        output = []

        for url in self._osd_urls(ip):
            result = xml.get_text(url)

            if not result.get("success"):
                output.append({
                    "url": url,
                    "success": False,
                    "status_code": result.get("status_code")
                })
                continue

            text = result.get("text", "")

            output.append({
                "url": url,
                "success": True,
                "date_enabled": xml.get_tag_value_inside_block(text, "DateTimeOverlay", "enabled"),
                "name_enabled": xml.get_tag_value_inside_block(text, "channelNameOverlay", "enabled"),
                "name": xml.get_tag_value_inside_block(text, "channelNameOverlay", "name")
            })

        return output

    def set_timezone(self, ip, username=None, password=None, timezone="CST-7:00:00"):
        auth = self._auth(username, password)
        url = f"http://{ip}/ISAPI/System/time"

        xml = XMLConfigEngine(auth)
        current = xml.get_text(url)

        if not current.get("success"):
            return {
                "success": False,
                "message": "GET XML time gagal",
                "status_code": current.get("status_code")
            }

        xml_text = xml.set_tag_value(
            current["text"],
            "timeZone",
            timezone
        )

        return xml.put_text(url, xml_text)
