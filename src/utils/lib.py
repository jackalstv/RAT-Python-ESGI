import struct
import socket

from src.utils.logger import setup_logger

log = setup_logger("lib")


def send_raw(sock, data):
    length = struct.pack(">I", len(data))
    sock.sendall(length + data)


def recv_raw(sock):
    header = _recv_exactly(sock, 4)
    if not header:
        raise ConnectionError("connexion fermee")
    length = struct.unpack(">I", header)[0]
    if length == 0:
        return b""
    return _recv_exactly(sock, length)


def _recv_exactly(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("socket fermee pendant reception")
        buf += chunk
    return buf


def send_msg(sock, data, key=None):
    if key:
        from src.utils.crypto import encrypt_msg

        data = encrypt_msg(key, data)
    send_raw(sock, data)


def recv_msg(sock, key=None):
    data = recv_raw(sock)
    if key:
        from src.utils.crypto import decrypt_msg

        data = decrypt_msg(key, data)
    return data
