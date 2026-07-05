class DeviceClassifier:

    def classify(self, vendor, open_ports):
        camera_vendors = [
            "Hikvision",
            "Dahua",
            "Uniview",
            "IP Camera",
            "RTSP Device"
        ]

        if vendor in camera_vendors:
            return "CAMERA"

        if 554 in open_ports:
            return "CAMERA"

        if vendor in ["MikroTik"]:
            return "ROUTER"

        if "Web Server" in vendor:
            return "SERVER"

        if 80 in open_ports or 443 in open_ports:
            return "NETWORK_DEVICE"

        return "UNKNOWN"
