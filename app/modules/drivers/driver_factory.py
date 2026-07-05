from app.modules.drivers.hikvision_driver import HikvisionDriver


class DriverFactory:

    def get_driver(self, vendor):

        vendor = (vendor or "").lower()

        if vendor == "hikvision":
            return HikvisionDriver()

        return None
