import pytest
from unittest.mock import MagicMock

from src.server.server import RATServer
from src.server.session import Session


def _fake_session(agent_id=0):
    sock = MagicMock()
    addr = ("10.0.0.1", 54321)
    key = b"\x00" * 32
    return Session(agent_id, sock, addr, key)


def test_session_str():
    sess = _fake_session(1)
    sess.hostname = "victim-pc"
    sess.os_info = "Linux"
    s = str(sess)
    assert "victim-pc" in s
    assert "10.0.0.1" in s


def test_server_add_remove():
    srv = RATServer()
    sess = _fake_session(0)
    srv.sessions[0] = sess

    assert srv.get_session(0) is sess
    assert len(srv.list_sessions()) == 1

    srv.remove_session(0)
    assert srv.get_session(0) is None
    assert len(srv.list_sessions()) == 0


def test_server_empty():
    srv = RATServer()
    assert srv.list_sessions() == []


def test_server_multiple():
    srv = RATServer()
    for i in range(3):
        srv.sessions[i] = _fake_session(i)

    sessions = srv.list_sessions()
    assert len(sessions) == 3
    ids = [s.id for s in sessions]
    assert set(ids) == {0, 1, 2}


def test_session_send_cmd():
    from src.utils.crypto import gen_keypair, derive_shared_key

    priv_a, pub_a = gen_keypair()
    priv_b, pub_b = gen_keypair()
    key = derive_shared_key(priv_a, pub_b)

    sock = MagicMock()
    sent = []
    sock.sendall = lambda data: sent.append(data)

    sess = Session(0, sock, ("127.0.0.1", 1234), key)
    sess.send_cmd("screenshot")

    assert len(sent) == 1
    assert len(sent[0]) > 4
