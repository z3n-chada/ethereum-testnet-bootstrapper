import argparse
from pathlib import Path
import shutil
import logging
import sys

from modules.TestnetBootstrapper import EthereumTestnetBootstrapper


def setup_logging(args):
    global logger
    logging_levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "critical": logging.CRITICAL,
        "error": logging.ERROR,
        "warning": logging.WARNING,
    }
    if args.log_level.lower() not in logging_levels:
        raise Exception(f"Got bad logging level: {args.log_level}")

    log_level = logging_levels[args.log_level.lower()]
    log_format = logging.Formatter("%(asctime)s: %(levelname)s: %(message)s")
    logger = logging.getLogger("bootstrapper_log")
    logger.setLevel(log_level)

    # logging.basicConfig(format=log_format, level=log_level)

    if args.log_to_stdout:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(log_level)
        stdout_handler.setFormatter(log_format)
        logger.addHandler(stdout_handler)
    if args.log_to_file:
        file_handler = logging.FileHandler(args.log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)

    logger.info("started the bootstrapper")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        dest="config",
        required=True,
        help="Which config file to use to create a testnet.",
    )

    parser.add_argument(
        "--write-docker-compose",
        dest="write_docker_compose",
        action="store_true",
        help="Write the docker-compose.yaml file to bootstrap the network",
    )

    parser.add_argument(
        "--clear-last-run",
        dest="clear_last_run",
        action="store_true",
        default=False,
        help="Clear the last run.",
    )

    parser.add_argument(
        "--init-bootstrapper",
        dest="init_bootstrapper",
        action="store_true",
        default=False,
        help="Init the files and dirs needed by the bootstrapper.",
    )

    parser.add_argument(
        "--bootstrap-testnet",
        dest="bootstrap_testnet",
        action="store_true",
        default=False,
        help="Start the testnet",
    )

    parser.add_argument(
        "--log-to-stdout",
        dest="log_to_stdout",
        action="store_true",
        default=True,
        help="add a log stream handler for stdout.",
    )

    parser.add_argument(
        "--log-to-file",
        dest="log_to_file",
        action="store_true",
        default=True,
        help="add a log stream handler for a file.",
    )

    parser.add_argument(
        "--log-file",
        dest="log_file",
        default="/source/data/bootstrapper.log",
        help="Log file destination for the bootstrapper.",
    )

    parser.add_argument(
        "--log-level",
        dest="log_level",
        default="info",
        help="logging level to use.",
    )

    args = parser.parse_args()

    setup_logging(args)

    etb = EthereumTestnetBootstrapper(args.config)
    if args.clear_last_run:
        etb.clear_last_run()

    if args.write_docker_compose:
        etb.write_docker_compose()

    elif args.bootstrap_testnet:
        etb.bootstrap_testnet()

    elif args.init_bootstrapper:
        etb.init_bootstrapper()
