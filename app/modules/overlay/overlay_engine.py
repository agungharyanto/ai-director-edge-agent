from datetime import datetime


class OverlayEngine:

    @staticmethod
    def build(camera):
        return {
            "court": camera["court_name"] if "court_name" in camera.keys() and camera["court_name"] else "-",
            "camera": camera["name"] or "-",
            "vendor": camera["vendor"] or "-",
            "model": camera["model"] or "-",
            "status": camera["provision_status"] or "-",
            "time": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        }
