"""Helpers for finding LAN URLs so tablets/phones can connect."""

import socket

DEFAULT_PORT = 5000


def get_lan_ips() -> list[str]:
    """Return local IPv4 addresses other devices on Wi‑Fi can use."""
    ips: set[str] = set()
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect(("8.8.8.8", 80))
        ips.add(probe.getsockname()[0])
        probe.close()
    except OSError:
        pass

    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ips.add(info[4][0])
    except OSError:
        pass

    ips.discard("127.0.0.1")
    return sorted(ips)


def get_device_urls(port: int = DEFAULT_PORT) -> list[str]:
    return [f"http://{ip}:{port}" for ip in get_lan_ips()]