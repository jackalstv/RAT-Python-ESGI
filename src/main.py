import argparse
import sys

from src.utils.logger import setup_logger

log = setup_logger("main")


def main():
    parser = argparse.ArgumentParser(description="RAT-Python")
    parser.add_argument("mode", choices=["server", "client"])
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)

    args = parser.parse_args()

    if args.mode == "server":
        from src.server.main import run_server

        run_server(host=args.host, port=args.port)
    elif args.mode == "client":
        from src.client.main import run_client

        run_client(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
