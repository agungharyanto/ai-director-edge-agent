import requests
import urllib3
import xml.etree.ElementTree as ET

from app.modules.drivers.base_driver import BaseDriver

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HikvisionDriver(BaseDriver):

    def probe(self, ip, username=None, password=None):
        return self.device_info(ip, username, password)

    def device_info(self, ip, username=None, password=None):
        urls = [
            f"http://{ip}/ISAPI/System/deviceInfo",
            f"https://{ip}/ISAPI/System/deviceInfo"
        ]

        auth = None
        if username and password:
            auth = requests.auth.HTTPDigestAuth(username, password)

        for url in urls:
            try:
                response = requests.get(
                    url,
                    timeout=3,
                    verify=False,
                    auth=auth
                )

                if response.status_code == 401:
                    return {
                        "vendor": "Hikvision",
                        "success": False,
                        "auth_required": True,
                        "status_code": 401,
                        "message": "Hikvision terdeteksi, tapi butuh username/password"
                    }

                if response.status_code != 200:
                    continue

                root = ET.fromstring(response.text)
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

    def hide_osd(self, ip, username=None, password=None):
        auth = None
        if username and password:
            auth = requests.auth.HTTPDigestAuth(username, password)

        url = f"http://{ip}/ISAPI/System/Video/inputs/channels/1/overlays"

        xml = """<?xml version="1.0" encoding="UTF-8"?>
<VideoOverlay version="2.0" xmlns="http://www.hikvision.com/ver20/XMLSchema">
<normalizedScreenSize>
<normalizedScreenWidth>704</normalizedScreenWidth>
<normalizedScreenHeight>576</normalizedScreenHeight>
</normalizedScreenSize>
<attribute>
<transparent>false</transparent>
<flashing>false</flashing>
</attribute>
<fontSize>adaptive</fontSize>
<TextOverlayList size="4">
</TextOverlayList>
<DateTimeOverlay>
<enabled>false</enabled>
<positionX>0</positionX>
<positionY>544</positionY>
<dateStyle>MM-DD-YYYY</dateStyle>
<timeStyle>24hour</timeStyle>
<displayWeek>false</displayWeek>
</DateTimeOverlay>
<channelNameOverlay version="2.0" xmlns="http://www.hikvision.com/ver20/XMLSchema">
<enabled>false</enabled>
<positionX>512</positionX>
<positionY>64</positionY>
<name></name>
</channelNameOverlay>
<frontColorMode>auto</frontColorMode>
<frontColor>000000</frontColor>
<alignment>customize</alignment>
<boundary>1</boundary>
<upDownboundary>0</upDownboundary>
<leftRightboundary>0</leftRightboundary>
</VideoOverlay>
"""

        try:
            response = requests.put(
                url,
                data=xml.encode("utf-8"),
                headers={"Content-Type": "application/xml"},
                auth=auth,
                timeout=5,
                verify=False
            )

            return {
                "success": response.status_code in [200, 201],
                "status_code": response.status_code,
                "response": response.text[:500]
            }

        except Exception as error:
            return {
                "success": False,
                "error": str(error)
            }
