import socket
import threading

from src.utils.logger import setup_logger
from src.utils.config import DEFAULT_HOST, DEFAULT_PORT

log = setup_logger("listener")


class Listener:
    def __init__(self, server, host=None, port=None):
        self.server = server
        self.host = host or DEFAULT_HOST
        self.port = port or DEFAULT_PORT
        self._sock = None
        self._running = False

    def start(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self._sock.listen(10)
        self._running = True
        log.info(f"Ecoute sur {self.host}:{self.port}")

        t = threading.Thread(target=self._accept_loop, daemon=True)
        t.start()

    def _accept_loop(self):
        while self._running:
            try:
                conn, addr = self._sock.accept()
                log.info(f"Nouvelle connexion {addr[0]}:{addr[1]}")
                threading.Thread(
                    target=self.server.handle_new_agent,
                    args=(conn, addr),
                    daemon=True,
                ).start()
            except OSError:
                break

    def stop(self):
        self._running = False
        if self._sock:
            self._sock.close()
