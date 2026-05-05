"""Send UDP packets to the speed display application.

The application listens on UDP port 3000 and expects a 2-byte payload:
    byte[0] = speed (taken modulo 100 by the application)
    byte[1] = failure flag (0 means OK, anything else means failure)
"""

import socket

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 3000


def send(speed: int, failure: bool, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    """Send one 2-byte packet to the application."""
    payload = bytes((speed & 0xFF, 1 if failure else 0))
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(payload, (host, port))


def send_raw(payload: bytes, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    """Send an arbitrary payload. Useful for malformed-input tests."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(payload, (host, port))
