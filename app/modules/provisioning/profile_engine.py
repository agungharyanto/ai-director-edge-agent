from app.modules.provisioning.profile_hikvision import HikvisionProfile


class ProfileEngine:

    def provision(self, vendor, driver, ip, username, password):
        vendor = (vendor or "").lower()

        if vendor == "hikvision":
            return HikvisionProfile().apply(driver, ip, username, password)

        return {
            "success": False,
            "steps": [],
            "message": f"Vendor belum didukung: {vendor}"
        }
