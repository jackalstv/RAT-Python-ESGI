import os
import base64
import json
import platform

from src.utils.logger import setup_logger
from src.utils.protocol import make_msg, OP_RESP, OP_ERROR, OP_FILE

log = setup_logger("cmd.files")


def cmd_download(path):
    path = path.strip()
    if not os.path.isfile(path):
        return make_msg(OP_ERROR, payload=f"Fichier introuvable: {path}")
    try:
        with open(path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        fname = os.path.basename(path)
        msg = json.dumps({"op": OP_FILE, "filename": fname, "data": b64}).encode()
        return msg
    except Exception as e:
        log.error(f"Erreur download {path}: {e}")
        return make_msg(OP_ERROR, payload=str(e))


def cmd_upload(remote_path, filename, data_b64):
    try:
        dest_dir = os.path.dirname(remote_path)
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)
        with open(remote_path, "wb") as f:
            f.write(base64.b64decode(data_b64))
        return make_msg(OP_RESP, payload=f"Fichier ecrit: {remote_path}")
    except Exception as e:
        log.error(f"Erreur upload vers {remote_path}: {e}")
        return make_msg(OP_ERROR, payload=str(e))


def cmd_search(name):
    name = name.strip()
    found = []
    if platform.system() == "Windows":
        start_dirs = ["C:\\"]
    else:
        start_dirs = ["/"]

    for start in start_dirs:
        for root, dirs, files in os.walk(start):
            dirs[:] = [d for d in dirs if d not in {"proc", "sys", "dev"}]
            for fname in files:
                if name.lower() in fname.lower():
                    found.append(os.path.join(root, fname))
                    if len(found) >= 100:
                        break
            if len(found) >= 100:
                break

    if not found:
        return make_msg(OP_RESP, payload=f"Aucun fichier trouve pour: {name}")

    result = "\n".join(found)
    if len(found) == 100:
        result += "\n... (tronque a 100)"
    return make_msg(OP_RESP, payload=result)
