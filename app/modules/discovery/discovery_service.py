import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.modules.discovery.ping_scanner import PingScanner
from app.modules.discovery.port_scanner import PortScanner


class DiscoveryService:

    DEFAULT_PORTS = [80, 443, 554, 8000, 8080, 8899]

    def __init__(self):
        self.ping_scanner = PingScanner()
        self.port_scanner = PortScanner()

    def scan_host(self, ip_address):
        ping_ok = self.ping_scanner.ping(ip_address)

        open_ports = []

        if ping_ok:
            for port in self.DEFAULT_PORTS:
                if self.port_scanner.check(ip_address, port):
                    open_ports.append(port)

        return {
            "ip_address": ip_address,
            "ping": "UP" if ping_ok else "DOWN",
            "ports": open_ports,
            "vendor": "Unknown",
            "model": "-"
        }

    def scan_network(self, network_cidr, max_workers=64):
        network = ipaddress.ip_network(network_cidr, strict=False)

        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.scan_host, str(ip)): str(ip)
                for ip in network.hosts()
            }

            for future in as_completed(futures):
                result = future.result()

                if result["ping"] == "UP" or result["ports"]:
                    results.append(result)

        results.sort(key=lambda item: tuple(map(int, item["ip_address"].split("."))))

        return results
