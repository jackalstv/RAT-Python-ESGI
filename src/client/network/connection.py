import socket
import threading
import time

from src.utils.logger import setup_logger
from src.utils.crypto import gen_keypair, derive_shared_key
from src.utils.lib import send_raw, recv_raw, send_msg, recv_msg
from src.utils.config import DEFAULT_CLIENT_HOST, DEFAULT_PORT, SOCKET_TIMEOUT

log = setup_logger("connection")

RETRY_DELAY = 10


class Connection:
    def __init__(self, host=None, port=None):
        self.host = host or DEFAULT_CLIENT_HOST
        self.port = port or DEFAULT_PORT
        self.sock = None
        self.key = None
        self._send_lock = threading.Lock()

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(SOCKET_TIMEOUT)
            self.sock.connect((self.host, self.port))
            log.info(f"Connecte a {self.host}:{self.port}")

            # ECDH : serveur envoie sa cle en premier
            server_pub = recv_raw(self.sock)
            priv, pub_bytes = gen_keypair()
            send_raw(self.sock, pub_bytes)
            self.key = derive_shared_key(priv, server_pub)
            log.debug("Echange ECDH OK")

            self.sock.settimeout(None)
            return True

        except Exception as e:
            log.error(f"Echec connexion: {e}")
            if self.sock:
                self.sock.close()
                self.sock = None
            return False

    def connect_with_retry(self):
        attempt = 0
        while True:
            attempt += 1
            log.info(f"Tentative #{attempt}...")
            if self.connect():
                return
            log.warning(f"Retry dans {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)

    def send(self, data):
        with self._send_lock:
            send_msg(self.sock, data, self.key)

    def recv(self):
        return recv_msg(self.sock, self.key)

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None
