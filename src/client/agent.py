import platform
import socket
import time

from src.utils.logger import setup_logger
from src.utils.protocol import make_msg, parse_msg, OP_RESP, OP_ERROR, OP_CMD
from src.client.network.connection import Connection

log = setup_logger("agent")


class Agent:
    def __init__(self, host=None, port=None):
        self.conn = Connection(host=host, port=port)

    def start(self):
        while True:
            try:
                self.conn.connect_with_retry()
                self._send_sysinfo()
                self._command_loop()
            except Exception as e:
                log.error(f"Erreur agent: {e}")
            finally:
                self.conn.close()
                time.sleep(10)

    def _send_sysinfo(self):
        info = {
            "os": platform.system() + " " + platform.release(),
            "hostname": socket.gethostname(),
            "arch": platform.machine(),
        }
        msg = make_msg(OP_RESP, payload=info)
        self.conn.send(msg)
        log.info("Sysinfo envoye")

    def _command_loop(self):
        log.info("En attente de commandes...")
        while True:
            try:
                raw = self.conn.recv()
            except ConnectionError as e:
                log.error(f"Connexion perdue: {e}")
                raise
            except Exception as e:
                log.error(f"Erreur recv: {e}")
                raise ConnectionError(str(e))

            msg = parse_msg(raw)
            if msg.get("op") != OP_CMD:
                continue

            cmd_str = msg.get("payload", "").strip()
            log.debug(f"Commande recue: {cmd_str}")

            try:
                resp = self._handle(cmd_str)
            except Exception as e:
                log.error(f"Erreur exec '{cmd_str}': {e}")
                resp = make_msg(OP_ERROR, payload=str(e))

            if resp:
                self.conn.send(resp)

    def _handle(self, cmd_str):
        return make_msg(OP_ERROR, payload=f"Commande inconnue: {cmd_str}")
