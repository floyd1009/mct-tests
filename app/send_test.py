import socket
import sys


speed = int(sys.argv[1]) if len(sys.argv) > 1 else 42
failure = int(sys.argv[2]) if len(sys.argv) > 2 else 0

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    sock.sendto(bytes((speed % 100, 1 if failure else 0)), ("127.0.0.1", 3000))

print(f"sent speed={speed % 100:02d} failure={1 if failure else 0}")