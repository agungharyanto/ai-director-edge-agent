class VendorDetector:

    def detect(self, http_data, open_ports):
        if http_data is None:
            if 554 in open_ports:
                return "RTSP Device", "-", 40
            return "Unknown", "-", 0

        title = (http_data.get("title") or "").lower()
        server = (http_data.get("server") or "").lower()

        if "hikvision" in title or "hikvision" in server:
            return "Hikvision", "-", 95

        if "dahua" in title or "dahua" in server:
            return "Dahua", "-", 95

        if "uniview" in title or "uniview" in server or "unv" in title:
            return "Uniview", "-", 90

        if "ubiquiti" in title or "unifi" in title:
            return "Ubiquiti", "-", 90

        if "mikrotik" in title or "routeros" in title:
            return "MikroTik", "-", 90

        if "apache" in server:
            return "Apache Web Server", "-", 60

        if "nginx" in server:
            return "Nginx Web Server", "-", 60

        if 554 in open_ports:
            return "IP Camera", "-", 50

        if 80 in open_ports or 443 in open_ports:
            return "Web Device", "-", 30

        return "Unknown", "-", 0
