import json

OP_CMD = "cmd"
OP_RESP = "resp"
OP_FILE = "file"
OP_DATA = "data"
OP_ERROR = "error"
OP_OK = "ok"
OP_STREAM = "stream"
OP_STREAM_END = "stream_end"


def make_msg(op, payload=None, filename=None):
    msg = {"op": op}
    if payload is not None:
        msg["payload"] = payload
    if filename:
        msg["filename"] = filename
    return json.dumps(msg).encode("utf-8")


def parse_msg(raw):
    return json.loads(raw.decode("utf-8"))


def make_file_msg(filename, data_b64):
    msg = {
        "op": OP_FILE,
        "filename": filename,
        "data": data_b64,
    }
    return json.dumps(msg).encode("utf-8")


def make_data_msg(data_b64, filename=None):
    msg = {"op": OP_DATA, "data": data_b64}
    if filename:
        msg["filename"] = filename
    return json.dumps(msg).encode("utf-8")
