import requests


class HikvisionProfile:

    def apply(self, driver, ip, username, password):
        steps = []

        osd_result = driver.hide_osd(ip, username, password)
        steps.append({
            "step": "Hide OSD + Reboot",
            "success": osd_result.get("success", False),
            "result": osd_result
        })

        timezone_result = driver.set_timezone(
            ip,
            username,
            password,
            timezone="CST-7:00:00"
        )
        steps.append({
            "step": "Set Timezone Asia/Jakarta",
            "success": timezone_result.get("success", False),
            "result": timezone_result
        })

        rtsp_url = driver.rtsp(ip, username, password)
        steps.append({
            "step": "Generate RTSP",
            "success": bool(rtsp_url)
        })

        return {
            "success": steps[0]["success"] and bool(rtsp_url),
            "steps": steps,
            "rtsp_url": rtsp_url,
            "note": "Camera reboot otomatis. Status AI READY valid setelah kamera hidup lagi 60-120 detik."
        }
