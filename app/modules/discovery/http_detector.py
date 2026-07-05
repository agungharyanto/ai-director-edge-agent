import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HTTPDetector:

    def extract_title(self, html):
        if not html:
            return ""

        lower = html.lower()

        if "<title>" not in lower:
            return ""

        try:
            start = lower.index("<title>") + len("<title>")
            end = lower.index("</title>")
            return html[start:end].strip()
        except Exception:
            return ""

    def probe(self, ip_address):
        targets = [
            f"http://{ip_address}",
            f"https://{ip_address}"
        ]

        for url in targets:
            try:
                response = requests.get(
                    url,
                    timeout=2,
                    verify=False
                )

                return {
                    "url": url,
                    "status": response.status_code,
                    "server": response.headers.get("Server", ""),
                    "title": self.extract_title(response.text)
                }

            except Exception:
                continue

        return None
