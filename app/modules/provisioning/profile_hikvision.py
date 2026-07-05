import requests


class HikvisionProfile:

    def apply(self, driver, ip, username, password):
        steps = []

        osd_result = driver.hide_osd(ip, username, password)
        steps.append({
            "step": "Hide OSD",
            "success": osd_result.get("success", False),
            "result": osd_result
        })

        snapshot_ok = False

        try:
            snapshot_url = driver.snapshot(ip, username, password)

            response = requests.get(
                snapshot_url,
                auth=requests.auth.HTTPDigestAuth(username, password),
                timeout=5,
                verify=False
            )

            snapshot_ok = response.status_code == 200 and len(response.content) > 1000

        except Exception:
            snapshot_ok = False

        steps.append({
            "step": "Verify Snapshot",
            "success": snapshot_ok
        })

        rtsp_url = driver.rtsp(ip, username, password)

        steps.append({
            "step": "Generate RTSP",
            "success": bool(rtsp_url)
        })

        return {
            "success": all(step["success"] for step in steps),
            "steps": steps,
            "rtsp_url": rtsp_url
        }
