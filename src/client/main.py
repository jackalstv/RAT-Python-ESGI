from src.utils.logger import setup_logger
from src.utils.config import DEFAULT_CLIENT_HOST, DEFAULT_PORT
from src.client.agent import Agent

log = setup_logger("client.main")


def run_client(host=None, port=None):
    host = host or DEFAULT_CLIENT_HOST
    port = port or DEFAULT_PORT
    log.info(f"Demarrage agent -> {host}:{port}")
    agent = Agent(host=host, port=port)
    agent.start()
