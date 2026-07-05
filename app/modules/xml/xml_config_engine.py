import re
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class XMLConfigEngine:

    def __init__(self, auth):
        self.auth = auth

    def get_text(self, url):
        try:
            r = requests.get(
                url,
                auth=self.auth,
                verify=False,
                timeout=5
            )

            return {
                "success": r.status_code == 200,
                "status_code": r.status_code,
                "text": r.text
            }

        except Exception as error:
            return {
                "success": False,
                "status_code": 0,
                "text": "",
                "error": str(error)
            }

    def put_text(self, url, xml_text):
        try:
            r = requests.put(
                url,
                data=xml_text.encode("utf-8"),
                headers={"Content-Type": "application/xml"},
                auth=self.auth,
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
                "status_code": 0,
                "error": str(error)
            }

    def set_tag_value(self, xml_text, tag, value):
        return re.sub(
            rf"<{tag}>(.*?)</{tag}>",
            f"<{tag}>{value}</{tag}>",
            xml_text,
            flags=re.DOTALL
        )

    def set_tag_value_inside_block(self, xml_text, block_tag, tag, value):
        pattern = rf"(<{block_tag}[^>]*>.*?</{block_tag}>)"

        def repl(match):
            block = match.group(1)
            return self.set_tag_value(block, tag, value)

        return re.sub(pattern, repl, xml_text, flags=re.DOTALL)

    def get_tag_value_inside_block(self, xml_text, block_tag, tag):
        block_match = re.search(
            rf"<{block_tag}[^>]*>.*?</{block_tag}>",
            xml_text,
            flags=re.DOTALL
        )

        if not block_match:
            return None

        tag_match = re.search(
            rf"<{tag}>(.*?)</{tag}>",
            block_match.group(0),
            flags=re.DOTALL
        )

        if not tag_match:
            return None

        return tag_match.group(1).strip()
