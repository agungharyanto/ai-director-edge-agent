import ipaddress
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.modules.discovery.ping_scanner import PingScanner
from app.modules.discovery.port_scanner import PortScanner
from app.modules.discovery.http_detector import HTTPDetector
from app.modules.discovery.vendor_detector import VendorDetector
from app.modules.discovery.classifier import DeviceClassifier
from app.modules.discovery.driver_manager import DriverManager
from app.repositories.discovery_repository import DiscoveryRepository
from app.modules.inventory.inventory_sync import InventorySync


class DiscoveryService:

    DEFAULT_PORTS = [80, 443, 554, 8000, 8080, 8899]

    def __init__(self):
        self.ping_scanner = PingScanner()
        self.port_scanner = PortScanner()
        self.http_detector = HTTPDetector()
        self.vendor_detector = VendorDetector()
        self.classifier = DeviceClassifier()
        self.driver_manager = DriverManager()

    def scan_host(self, ip_address):
        ping_ok = self.ping_scanner.ping(ip_address)
        open_ports = []

        if ping_ok:
            for port in self.DEFAULT_PORTS:
                if self.port_scanner.check(ip_address, port):
                    open_ports.append(port)

        http_data = None

        if 80 in open_ports or 443 in open_ports:
            http_data = self.http_detector.probe(ip_address)

        vendor, model, confidence = self.vendor_detector.detect(
            http_data,
            open_ports
        )

        firmware = None
        serial = None
        mac = None

        driver_result = self.driver_manager.detect(ip_address, open_ports)

        if driver_result:
            vendor = driver_result.get("vendor", vendor)
            model = driver_result.get("model") or model
            firmware = driver_result.get("firmware")
            serial = driver_result.get("serial")
            mac = driver_result.get("mac")
            confidence = 99 if driver_result.get("success") else 80

        device_type = self.classifier.classify(
            vendor,
            open_ports
        )

        return {
            "ip_address": ip_address,
            "ping": "UP" if ping_ok else "DOWN",
            "ports": open_ports,
            "vendor": vendor,
            "model": model,
            "confidence": confidence,
            "device_type": device_type,
            "firmware": firmware,
            "serial": serial,
            "mac": mac
        }

    def start_scan(self, network_cidr):
        network = ipaddress.ip_network(network_cidr, strict=False)
        hosts = [str(ip) for ip in network.hosts()]

        repo = DiscoveryRepository()
        job_id = repo.create_job(network_cidr, len(hosts))

        thread = threading.Thread(
            target=self.run_scan,
            args=(job_id, hosts),
            daemon=True
        )
        thread.start()

        return job_id

    def run_scan(self, job_id, hosts):
        scanned = 0
        found = 0
        repo = DiscoveryRepository()

        with ThreadPoolExecutor(max_workers=64) as executor:
            futures = {
                executor.submit(self.scan_host, ip): ip
                for ip in hosts
            }

            for future in as_completed(futures):
                result = future.result()
                scanned += 1

                if result["ping"] == "UP" or result["ports"]:
                    found += 1

                    repo.add_result(
                        job_id=job_id,
                        ip_address=result["ip_address"],
                        ping_status=result["ping"],
                        open_ports=result["ports"],
                        vendor=result["vendor"],
                        model=result["model"],
                        confidence=result["confidence"]
                    )

                    InventorySync().sync_discovery_result({
                        "ip_address": result["ip_address"],
                        "ping_status": result["ping"],
                        "open_ports": ",".join(str(port) for port in result["ports"]),
                        "vendor": result["vendor"],
                        "model": result["model"],
                        "device_type": result["device_type"],
                        "firmware": result.get("firmware"),
                        "serial": result.get("serial"),
                        "mac": result.get("mac")
                    })

                repo.update_progress(job_id, scanned, found)

        repo.finish_job(job_id)
