import pytest
import socket

from src.utils.crypto import gen_keypair, derive_shared_key, encrypt_msg, decrypt_msg
from src.utils.protocol import make_msg, parse_msg, OP_CMD, OP_RESP


def test_ecdh_shared_key():
    priv_a, pub_a = gen_keypair()
    priv_b, pub_b = gen_keypair()

    key_a = derive_shared_key(priv_a, pub_b)
    key_b = derive_shared_key(priv_b, pub_a)

    assert key_a == key_b
    assert len(key_a) == 32


def test_encrypt_decrypt():
    priv_a, pub_a = gen_keypair()
    priv_b, pub_b = gen_keypair()
    key = derive_shared_key(priv_a, pub_b)

    plaintext = b"message secret"
    ct = encrypt_msg(key, plaintext)
    result = decrypt_msg(key, ct)
    assert result == plaintext


def test_nonce_uniqueness():
    priv_a, pub_a = gen_keypair()
    priv_b, pub_b = gen_keypair()
    key = derive_shared_key(priv_a, pub_b)

    msg = b"test nonce"
    ct1 = encrypt_msg(key, msg)
    ct2 = encrypt_msg(key, msg)
    assert ct1 != ct2


def test_wrong_key_fails():
    priv_a, pub_a = gen_keypair()
    priv_b, pub_b = gen_keypair()
    priv_c, pub_c = gen_keypair()

    key_ab = derive_shared_key(priv_a, pub_b)
    key_ac = derive_shared_key(priv_a, pub_c)

    ct = encrypt_msg(key_ab, b"secret")
    with pytest.raises(Exception):
        decrypt_msg(key_ac, ct)


def test_make_parse():
    raw = make_msg(OP_CMD, payload="shell ls")
    parsed = parse_msg(raw)
    assert parsed["op"] == OP_CMD
    assert parsed["payload"] == "shell ls"


def test_make_msg_no_payload():
    raw = make_msg(OP_RESP)
    parsed = parse_msg(raw)
    assert parsed["op"] == OP_RESP
    assert "payload" not in parsed


def test_make_msg_filename():
    raw = make_msg(OP_RESP, payload="ok", filename="test.txt")
    parsed = parse_msg(raw)
    assert parsed["filename"] == "test.txt"


def test_framing_roundtrip():
    from src.utils.lib import send_raw, recv_raw

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]

    cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cli.connect(("127.0.0.1", port))
    conn, _ = srv.accept()

    data = b"hello framing"
    send_raw(cli, data)
    received = recv_raw(conn)

    assert received == data

    cli.close()
    conn.close()
    srv.close()
