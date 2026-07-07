import socket


class PortScanner:

    def check(self, ip_address, port, timeout=0.5):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)

            result = sock.connect_ex((ip_address, port))

            sock.close()

            return result == 0

        except Exception:
            return False
